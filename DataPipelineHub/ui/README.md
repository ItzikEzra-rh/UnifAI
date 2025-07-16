TBDs:

1. create a docker ignore to not copy unneeded files/folders into the docker when building
2. create a nginx configuration that fits sso.
3. in package.json that was the scripts section:

  "scripts": {
    "dev": "NODE_ENV=development tsx server/index.ts",
    "build": "vite build && esbuild server/index.ts --platform=node --packages=external --bundle --format=esm --outdir=dist",
    "start": "NODE_ENV=production node dist/index.js",
    "check": "tsc",
    "db:push": "drizzle-kit push"
  },

  
  change the nginx that once we see the 13456 (from env ) - send to the real BE
  when seeing 5001 (from env) send to multiagent be


package.json

includes all packages needed for our app
includes scripts part, in this part when we run a builder/installer it goes to the scripts part and if the arguments are there it takes it .
for example:


  "scripts": {
    "build:frontend": "vite build",
    "build": "pnpm run build:frontend",
  }

  when we run 'pnpm build' it first goes to the scripts part and sees that it needs to run the command: pnpm run build:frontend
  which in turn changes the build:frontend to vite build , so, the actual final command is 'pnpm run vite build'

lock files

lock files are a more specific package deps files. in package json we usually give a range or general rules as to what versions are allowed/required. but when we actually install the packages we get specific versions, this is listed in the lock files, it allows us to use them as the base for future installations and prevent conflicts and problems due to version issues



nginx configurations

rewrite vs. return vs. proxy_pass

* proxy_pass - will just redirect the call to the location set
* rewrite - works internally, the nginx will get the call, change according to the setting and will resume sending the call to the new updated location
* return - nginx will return the status requested (in this case 3XX) and the url the client needs to now redirect to.

when using the redirect from the axios
the rewrite means that we'll reach the route, hence we only need the address of the route and the port isn't needed.

when using directly to reach the BE, we want that anything of BE_port will reach the same route


NOTE: using the notebook namespace measn that routes/services aren't always available from outside the setup.





UI build flow - dev


UI build flow - production

corepack enable          # Enable Corepack (Node.js 16.10+)
corepack prepare pnpm@latest --activate # Install pnpm via Corepack

cd ui/
rm -f package-lock.json yarn.lock # Remove old lockfiles
rm -rf node_modules              # Remove existing node_modules
pnpm install 

...
here - set configurations in .json files
...

pnpm build



podman building

Optional: clean the podman images and containers from irrelevant 

for cont in $(podman ps -a --external |awk '{print $1}'); do podman rm -f $cont ; done
for image in $(podman images | grep none |awk '{print $3}'); do podman rmi  $image ; done

cd ./helm/ui
podman build -f Dockerfile -t unifai-ui .
podman tag localhost/unifai-ui images.paas.redhat.com/unifai/ui
podman push images.paas.redhat.com/unifai/ui