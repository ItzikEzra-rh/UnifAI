## Building the UI 

### pre-reqs

pnpm installed on your system

- upgrade your npm
  `npm install -g npm`

- install pnpm via corepack (can be done via npmn as well instead)
   `npm install -g corepack`
   `corepack enable`

- Install pnpm via Corepack
   `corepack prepare pnpm@latest --activate`


### install all required packages and build

- make sure you have the package.json and  pnpm-lock.yaml file in place, this sould come with the cloning and should be under the ui main folder.
  if you need to add a new package though don't foget to push the new lock file as well


- Install all dependencies (including devDependencies needed for the build). `--frozen-lockfile` ensures reproducible builds based on pnpm-lock.yaml.
  the lock file is the output of the last successful installation and we should use it, unless we specifically need to change packages or versions.
  `pnpm install --frozen-lockfile`

- build the UI
  `pnpm build`



## Running the UI

As we use usally existing backend or local ones depending on our work, we need a quick method to change the BEs we run against.
till now we used to update axios config, this works properly but with some caveats:
1. the changes must be removed before building the code so the axios won't change the UI behavior
2. every change needs a rebuild if we want to check the UI as a package
3. if we need to have a common api structure this might be complicated.

Instead of using axios, we need to change the usage to vite.config.ts proxies. this is build for  development env.
the vite.config.ts isn't going into the code so it's safe to build it, that way if the axios already have some config we just need to adjust the config to fit it (just like nginx config)


## analyzing the UI build

In order to analyze the UI build bundle we need a build analyzer tool, sine vite (the tool for building and serving) is using rollup we can use the rollup-plugin-visualizer

1. start by installing the plugin
  `pnpm add -D rollup-plugin-visualizer`

2. update teh vite.config.ts file with the plugin:



## Appendixes


### UI building infra

 - package.json

   includes all packages needed for our app
   includes scripts part, in this part when we run a builder/installer it goes to the scripts part and if the arguments are there it takes it .
   for example:

    `
    "scripts": {
      "build:frontend": "vite build",
      "build": "pnpm run build:frontend",
    }
    `

   when we run 'pnpm build' or 'pnpm run build' it first goes to the scripts part and sees that it needs to run the command: pnpm run build:frontend
   which in turn changes the build:frontend to vite build , so, the actual final command is 'pnpm run vite build'
   NOTE: if your scripts line invludes pnpm run <command> this will send the pnpm again to the scripts part to look for a line names <command>

 - lock files

   lock files are a more specific package deps files. in package json we usually give a range or general rules as to what versions are allowed/required. but when we actually install the packages we get specific versions, this is listed in the lock files, it allows us to use them as the base for future installations and prevent conflicts and problems due to version issues


TBDs:

1. create a docker ignore to not copy unneeded files/folders into the docker when building
3. in package.json that was the scripts section:

  "scripts": {
    "dev": "NODE_ENV=development tsx server/index.ts",
    "build": "vite build && esbuild server/index.ts --platform=node --packages=external --bundle --format=esm --outdir=dist",
    "start": "NODE_ENV=production node dist/index.js",
    "check": "tsc",
    "db:push": "drizzle-kit push"
  },





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