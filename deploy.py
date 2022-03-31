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


# temporary testing

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



















