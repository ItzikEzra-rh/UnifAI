## 

## Nginx dynamic configuration 

Nginx doesn't support environment variables in its configuration files. In order to make the nginx configuarion dynamic the common practice is to use some templating tool, most commonly envsubst
for that we've created the nginx.conf.template in this folder.
when the nginx container starts we first run the envsubst command which creates the actual config file and only after that we start the nginx.

NOTE: env subset might somtime replace strings not desired, for example in our config we have a $uri, naturaly, envsubst will replce this with the env uri (which doesn't exist in our case).
In order to overcome this we create a special env DOLLAR just to allow us to write ${DOLLAR}uri instead in the templare


## Nginx configurations

rewrite vs. return vs. proxy_pass

* proxy_pass - will just redirect the call to the location set
* rewrite - works internally, the nginx will get the call, change according to the setting and will resume sending the call to the new updated location
* return - nginx will return the status requested (in this case 3XX) and the url the client needs to now redirect to.

when using the redirect from the axios
the rewrite means that we'll reach the route, hence we only need the address of the route and the port isn't needed.

NOTE: a listener to the BE ports wasn't added as we don't use the nginx as the proxy for the BEs directly but only when going through the UI
It's possible to add it upon need.


NOTE: using the notebook namespace means that routes/services aren't always available from outside the setup. hence use the pipeline or the runtime, namespace