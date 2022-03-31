import time
import os
import re
import deploymentutils as du
from os.path import join as pjoin


from ipydex import IPS, activate_ips_on_exception

# simplify debugging
activate_ips_on_exception()


"""
This script serves to deploy and maintain the django application with which it is delivered.
It is largely based on this tutorial: <https://lab.uberspace.de/guide_django.html>.
"""


# call this before running the script:
# eval $(ssh-agent); ssh-add -t 10m


# this file must be changed according to your uberspace accound details (machine name and user name)
cfg = du.get_nearest_config("config-production.ini")


remote = cfg("remote_hostname")
user = cfg("user")

asset_dir = pjoin(du.get_dir_of_this_file(), "files")  # contains the templates and the direct upload files
upload_dir = pjoin(asset_dir, "root-dir")  # contains the direct upload files
temp_workdir = pjoin(du.get_dir_of_this_file(), "tmp_workdir")  # this will be deleted/overwritten


project_src_path = os.path.dirname(du.get_dir_of_this_file())



du.argparser.add_argument(
    "--dbg", action="store_true", help="start interactive shell for debugging. Then exit"
)



args = du.parse_args()

final_msg = f"Deployment script {du.bgreen('done')}."

if not args.target == "remote":
    raise NotImplementedError

# this is where the code will live after deployment
target_deployment_path = cfg("deployment_path")
static_root_dir = f"{target_deployment_path}/collected_static"
debug_mode = False

# print a warning for data destruction
du.warn_user(
    cfg("PROJECT_NAME"),
    args.target,
    args.unsafe,
    deployment_path=target_deployment_path,
    user=user,
    host=remote,
)

# ensure clean workdir
os.system(f"rm -rf {temp_workdir}")
os.makedirs(temp_workdir)

# exit(0)

c = du.StateConnection(remote, user=user, target=args.target)


c.run(f"mkdir -p {target_deployment_path}")

if 0:


    # prepare server
    c.chdir("~")
    c.run(f"apt update")  # update package db
    c.run(f"apt upgrade")  # ensure newest version of all packages
    c.run(f"apt install --yes {cfg('install_packages')}")


    # install starship
    c.run("mkdir -p ~/tmp")
    c.run("mkdir -p ~/bin")
    c.run("curl  https://starship.rs/install.sh > ~/tmp/install_starship.sh")
    c.run("sh ~/tmp/install_starship.sh -b ~/bin --yes")

    cmd = """cat <<EOT >> ~/.bashrc
    # make bash autocomplete with up/down arrow if in inteactive mode
    if [ -t 1 ]
    then
        bind '"\e[A":history-search-backward'
        bind '"\e[B":history-search-forward'
    fi

    eval "\$(~/bin/starship init bash)"

    export EDITOR=mcedit
    export VISUAL=mcedit
    EOT
    """

    c.run(cmd)


    # install backend


    c.run(f"git clone https://gitlab.com/TIBHannover/orkg/orkg-backend.git")
    c.chdir("~/orkg-backend")
    c.run(f"./gradlew jibDockerBuild")
    c.run(f"docker-compose up -d")


    # upload files
    c.run(f"rm -f /etc/nginx/sites-enabled/*")
    print("\n", "upload all files", "\n")
    if not upload_dir.endswith("/"):
        upload_dir = f"{upload_dir}/"
    c.rsync_upload(upload_dir, target_deployment_path, additional_flags="--links", target_spec="remote")
    c.run(f"systemctl restart nginx")


    # wait for all containers to come up
    time.sleep(60)
    # test if backend is running
    res = c.run(f"curl localhost:8080")
    assert "REST API" in res.stdout


    # install frontend
    # docker oder nativ ? -> nativ

    c.chdir("~")
    c.run("git clone https://gitlab.com/TIBHannover/orkg/orkg-frontend.git")
    c.chdir("~/orkg-frontend")
    # c.run("cp default.env .env")

    # upload local .env file
    c.rsync_upload(upload_dir, target_deployment_path, additional_flags="--links", target_spec="remote")

    # install nvm, node and yarn
    # 1. nvm
    c.run(f"curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash")

    # ensure that nvm installation works
    c.run("source ~/.nvm/nvm.sh; nvm --version")

    # 2. node
    c.run("source ~/.nvm/nvm.sh; nvm install v16.4.0")

    # 3. yarn
    c.run('curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -')
    c.run('echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list')
    c.run('sudo apt update')
    # ignore recommended node-dependency because we use nvm
    c.run('sudo apt install --no-install-recommends yarn')

    # build the frontend

    c.chdir("~/orkg-frontend")

    # upload local .env-file
    env_path = pjoin(du.get_dir_of_this_file(), "orkg-frontend", ".env")
    c.rsync_upload(env_path, "/root/orkg-frontend/.env", target_spec="remote")

    c.chdir("~/orkg-frontend")
    c.run('source ~/.nvm/nvm.sh; yarn')
    c.run('source ~/.nvm/nvm.sh; yarn build')

# ---

c.chdir("~/orkg-frontend")
c.run('rm -rf /var/www/html/fe/build')
c.run('cp -r build /var/www/html/fe/build')


#IPS()



exit(0)


# upload files
c.run(f"rm -f /etc/nginx/sites-enabled/*")
print("\n", "upload all files", "\n")
if not upload_dir.endswith("/"):
    upload_dir = f"{upload_dir}/"
c.rsync_upload(upload_dir, target_deployment_path, additional_flags="--links", target_spec="remote")
c.run(f"systemctl restart nginx")


exit(0)

# überflüssig
c.run(f"./gradlew bootRun")
exit(0)





























def create_and_setup_venv(c):

    c.run(f"{pipc} install --user virtualenv")

    print("create and activate a virtual environment inside $HOME")
    c.chdir("~")

    c.run(f"rm -rf {venv}")
    c.run(f"virtualenv -p {python_version} {venv}")

    c.activate_venv(f"~/{venv}/bin/activate")

    c.run(f"pip install --upgrade pip")
    c.run(f"pip install --upgrade setuptools")

    print("\n", "install uwsgi", "\n")
    c.run(f"pip install uwsgi")

    # ensure that the same version of deploymentutils like on the controller-pc is also in the server
    c.deploy_this_package()


def render_and_upload_config_files(c):

    c.activate_venv(f"~/{venv}/bin/activate")

    # generate the general uwsgi ini-file
    tmpl_dir = os.path.join("uberspace", "etc", "services.d")
    tmpl_name = "template_PROJECT_NAME_uwsgi.ini"
    target_name = "PROJECT_NAME_uwsgi.ini".replace("PROJECT_NAME", project_name)
    du.render_template(
        tmpl_path=pjoin(asset_dir, tmpl_dir, tmpl_name),
        target_path=pjoin(temp_workdir, tmpl_dir, target_name),
        context=dict(venv_abs_bin_path=f"{venv_path}/bin/", project_name=project_name),
    )

    # generate config file for django uwsgi-app
    tmpl_dir = pjoin("uberspace", "uwsgi", "apps-enabled")
    tmpl_name = "template_PROJECT_NAME.ini"
    target_name = "PROJECT_NAME.ini".replace("PROJECT_NAME", project_name)
    du.render_template(
        tmpl_path=pjoin(asset_dir, tmpl_dir, tmpl_name),
        target_path=pjoin(temp_workdir, tmpl_dir, target_name),
        context=dict(
            venv_dir=f"{venv_path}", deployment_path=target_deployment_path, port=port, user=user
        ),
    )

    #
    # ## upload config files to remote $HOME ##
    #
    srcpath1 = os.path.join(temp_workdir, "uberspace")
    filters = "--exclude='**/README.md' --exclude='**/template_*'"  # not necessary but harmless
    c.rsync_upload(srcpath1 + "/", "~", filters=filters, target_spec="remote")


def update_supervisorctl(c):

    c.activate_venv(f"~/{venv}/bin/activate")

    c.run("supervisorctl reread", target_spec="remote")
    c.run("supervisorctl update", target_spec="remote")
    print("waiting 10s for uwsgi to start")
    time.sleep(10)

    res1 = c.run("supervisorctl status", target_spec="remote")

    assert "uwsgi" in res1.stdout
    assert "RUNNING" in res1.stdout


def set_web_backend(c):
    c.activate_venv(f"~/{venv}/bin/activate")

    c.run(
        f"uberspace web backend set {django_url_prefix} --http --port {port}", target_spec="remote"
    )

    # note 1: the static files which are used by django are served under '{static_url_prefix}'/
    # (not {django_url_prefix}}{static_url_prefix})
    # they are served by apache from ~/html{static_url_prefix}, e.g. ~/html/markpad1-static

    c.run(f"uberspace web backend set {static_url_prefix} --apache", target_spec="remote")


def upload_files(c):
    print("\n", "ensure that deployment path exists", "\n")
    c.run(f"mkdir -p {target_deployment_path}")

    c.activate_venv(f"~/{venv}/bin/activate")

    print("\n", "upload config file", "\n")
    c.rsync_upload(cfg.path, target_deployment_path, target_spec="remote")

    c.chdir(target_deployment_path)

    print("\n", "upload current application files for deployment", "\n")
    # omit irrelevant files (like .git)
    # TODO: this should be done more elegantly
    filters = f"--exclude='.git/' " f"--exclude='.idea/' " f"--exclude='db.sqlite3' " ""

    c.rsync_upload(
        project_src_path + "/", target_deployment_path, filters=filters
    )

    c.run(f"touch requirements.txt", target_spec="remote")


def purge_deployment_dir(c):
    if not args.omit_backup:
        print(
            "\n",
            du.bred("  The `--purge` option explicitly requires the `--omit-backup` option. Quit."),
            "\n",
        )
        exit()
    else:
        answer = input(f"purging <{args.target}>/{target_deployment_path} (y/N)")
        if answer != "y":
            print(du.bred("Aborted."))
            exit()
        c.run(f"rm -r {target_deployment_path}")


def install_app(c):
    c.activate_venv(f"~/{venv}/bin/activate")

    c.chdir(target_deployment_path)
    c.run(f"pip install -r requirements.txt")


def initialize_db(c):

    c.chdir(target_deployment_path)
    c.run("python manage.py makemigrations")

    # This deletes all data (OK for this app but probably not OK for others) -> backup db before

    # print("\n", "backup old database", "\n")
    # res = c.run('python manage.py savefixtures')

    # delete old db
    c.run("rm -f db.sqlite3")

    # this creates the new database
    c.run("python manage.py migrate")

    # print("\n", "install initial data", "\n")
    # c.run(f"python manage.py loaddata {init_fixture_path}")


def generate_static_files(c):

    c.chdir(target_deployment_path)

    c.run("python manage.py collectstatic --no-input", target_spec="remote")

    print("\n", "copy static files to the right place", "\n")
    c.chdir(f"/var/www/virtual/{user}/html")
    c.run(f"rm -rf ./{static_url_prefix}")
    c.run(f"cp -r {static_root_dir} ./{static_url_prefix}")

    c.chdir(target_deployment_path)


def run_tests(c):
    c.chdir(target_deployment_path)
    print("\n", "run tests", "\n")
    c.run(f"python manage.py test {app_name}")


if args.dbg:
    c.activate_venv(f"{venv_path}/bin/activate")

    # c.deploy_local_package("/home/ck/projekte/rst_python/ipydex/repo")

    IPS()
    exit()

if args.initial:

    # create_and_setup_venv(c)
    render_and_upload_config_files(c)
    update_supervisorctl(c)
    set_web_backend(c)


upload_files(c)

if not args.omit_requirements:
    install_app(c)

if not args.omit_database:
    initialize_db(c)

if not args.omit_static:
    generate_static_files(c)

if not args.omit_tests:
    run_tests(c)

print("\n", "restart uwsgi service", "\n")
c.run(f"supervisorctl restart all", target_spec="remote")


print(final_msg)
