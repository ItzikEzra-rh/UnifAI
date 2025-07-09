#FROM  registry.access.redhat.com/ubi9/nodejs-18-minimal as build
FROM  registry.access.redhat.com/ubi9/nodejs-22 as build
#create a working folder
WORKDIR /ui

RUN npm install -g npm
RUN npm --version
#install pnpm via corepack (can be done via npmn as well instead)
RUN npm install -g corepack
RUN corepack enable                         
RUN corepack prepare pnpm@latest --activate # Install pnpm via Corepack


#copy the package.json and pnpm-lock.yaml files to the working folder
COPY package.json pnpm-lock.yaml ./
# Install all dependencies (including devDependencies needed for the build).
# `--frozen-lockfile` ensures reproducible builds based on pnpm-lock.yaml.
RUN pnpm install --frozen-lockfile

#copy the rest of the project files to the working folder
COPY . .

# Run our combined build command.
# As per your package.json, this builds:
# - Frontend (Vite) to /ui/build
# - Backend (esbuild) to /app/dist/server - not being used
RUN pnpm build



FROM registry.access.redhat.com/ubi9/nginx-120 as serve
RUN whoami
USER root
#Install debugging tools
RUN dnf update -y && dnf install -y vim less iputils telnet && dnf clean all
USER default
COPY --from=build /ui/build /usr/share/nginx/html

EXPOSE 8080
#HEALTHCHECK CMD curl --fail http://localhost:8080 || exit 1
#RUN ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log 
CMD ["nginx", "-g", "daemon off;"]