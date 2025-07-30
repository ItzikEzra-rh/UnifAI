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

- make sure you have the package.json and  pnpm-lock.yaml file in place, this should come with the cloning and should be under the ui main folder.
  **NOTE: if you need to add a new package though don't foרget to push the new lock file as well**


- Install all dependencies (including devDependencies needed for the build). `--frozen-lockfile` ensures reproducible builds based on pnpm-lock.yaml.
  the lock file is the output of the last successful installation and we should use it, unless we specifically need to change packages or versions.
  `pnpm install --frozen-lockfile`


- build the UI
  `pnpm build`



## Running the UI (locally)

As we use usally existing backend or local ones depending on our work, we need a quick method to change the BEs we run against.
till now we used to update axios config, this works properly but with some caveats:
1. the changes must be removed before building the code so the axios won't change the UI behavior
2. every change needs a rebuild if we want to check the UI as a package
3. if we need to have a common api structure this might be complicated.

Instead of using axios, we need to change the usage to vite.config.ts proxies. this is build for  development env.
the vite.config.ts isn't going into the code so it's safe to build it, that way if the axios already have some config we just need to adjust the config to fit it (just like nginx config)

In order to run the UI locally follow these steps:

1. update vite.config.ts server/proxy section to route the requests properly to the backends and replace the api1/api2 from the UI
   this step is crucial as it simulates the nginx behavior that we use in production (see example below):

   ```
    server: {
      port: 5173, // Or whatever port Vite is running on by default
      proxy: {
        // Proxy for api1
        '/api1': {
          target: 'http://<dataflow_be_address>:<dataflow_be_port>',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api1/, '/api'), // This rewrites /api1 to /api
          secure: false, // Set to true for production if target is HTTPS and has valid cert.
                        // Set to false for dev if you're getting SSL errors with self-signed or invalid certs.
        },
        // Proxy for api2 (assuming this is still local or another service)
        '/api2': {
          target: 'http://<multiagent_be_address>:<multiagent_be_port>',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api2/, '/api'), // This rewrites /api2 to nothing
          // secure: false, // Only needed if this target is HTTPS and you have SSL issues
        },
        // You can add more proxies here if needed
      }
    },
   ```


## analyzing the UI build (Optional)

In order to analyze the UI build bundle we need a build analyzer tool, since vite (the tool for building and serving) is using rollup we can use the rollup-plugin-visualizer

1. start by installing the plugin
  `pnpm add -D rollup-plugin-visualizer`

**NOTE: Currently the vite is being enabled only when building locally (when env var NODE_ENV !== "production"), in order to run the analyzer set the NODE_ENV="development" after the build a new file will be created and opened automatically analyzing the bundle of the UI**



## Appendixes


### UI building infra

#### Tools
  pnpm - package manager
  vite - code building and serving tool

#### Important files

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
   NOTE: if your scripts line includes pnpm run <command> this will send the pnpm again to the scripts part to look for a line names <command>

 - pnpm-lock.yaml

   lock files are a more specific package deps files. in package json we usually give a range or general rules as to what versions are allowed/required. but when we actually install the packages we get specific versions, this is listed in the lock files, it allows us to use them as the base for future installations and prevent conflicts and problems due to version issues

   In our case since we use pnpm the lock file to use is pnpm-lock.yaml

   **NOTE: If you need to update a package an reinstall you'll need to update the lock file (or run install to overwrite the lock file and push it after install  + build are successful)**

 - vite.config.ts

   As we use vite as the build tool we need to have the vite configuration file set. In it we set the input/output folders, proxies and plugins we want to use during our build, the syntax is typescript.


