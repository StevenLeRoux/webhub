#WebHub

WebHub is a lightweight set of tool to manage your different vhosts among different reverse proxies (rpxy) and among different environnments.

It provides and abstraction database of vhost (WebHub.conf) which makes possible to generate configurations for different rpxy technologies.

## WebHub.conf
```
version ...

node      nd-1     pool-dc1
node      nd-2     pool-dc2

generic        ap-1    nd-1
generic        ap-2    nd-2

service           ap-1    10.1.1.1    nd-1
service           ap-2    10.1.1.2    nd-2
service           ap-3    10.1.1.3    nd-1
service           ap-4    10.1.1.4    nd-2

worker         tc-1    10.1.2.1    pool-dc1
worker         tc-2    10.1.2.2    pool-dc2
worker         tc-3    10.1.2.3    pool-dc1
worker         tc-4    10.1.2.4    pool-dc2


########### sample.apps.domain.tld #####################
frontend    sample.apps.domain.tld-8080    http://ap-1:8080/
frontend    sample.apps.domain.tld-8080    http://ap-2:8080/
backend     sample.apps.domain.tld-8080    (key:criterion)  http://40000tc1@tc-1:40000/lb.jsp 1
backend     sample.apps.domain.tld-8080    (key:criterion)  http://40000tc2@tc-2:40000/lb.jsp 1
alias       sample.apps.domain.tld-8080    alias [alias]
balancerto  sample.apps.domain.tld-8080    0
backento    sample.apps.domain.tld-8080    30
nocompress  sample.apps.domain.tld-8080    swf|webp|pdf
rewrite     sample.apps.domain.tld-8080    "^match$" "newone"
forensic    sample.apps.domain.tld-8080
redirect    sample.apps.domain.tld-8080    "^match$"   "http://google.com"   ("VAR:condition")
expire      sample.apps.domain.tld-8080    "^match$" 10
nofailover  sample.apps.domain.tld-8080    on
hostport    sample.apps.domain.tld-8080    on
xdomain     sample.apps.domain.tld-8080    ['url'(,'url')*]
pxysrcaddr  sample.apps.domain.tld-8080    off
setcookie   sample.apps.domain.tld-8080    on
cache       sample.apps.domain.tld-8080    "^.*\.file_extention$"       public  7200
nocache     sample.apps.domain.tld-8080    on
sorry       sample.apps.domain.tld-8080    <IP>


########### sample2.apps.domain.tld #####################
frontend    sample2.apps.domain.tld-8080    http://ap-3:8080/
frontend    sample2.apps.domain.tld-8080    http://ap-4:8080/
backend     sample2.apps.domain.tld-8080    http://40001tc3@tc-3:40001/lb.jsp 
backend     sample2.apps.domain.tld-8080    http://40001tc4@tc-4:40001/lb.jsp 


```

### Todo

#### Browser Cache

Precise the use of default cache profile or disable caching or disable and precise which file you want to be cached in the browser.
So you have three cache profiles :

```
cache       sample.apps.domain.tld-8080    default   // use default cache profile
````
or
````
nocache     sample.apps.domain.tld-8080    on
````
or
````
nocache     sample.apps.domain.tld-8080    on
cache       sample.apps.domain.tld-8080    "^.*\.file_extention$"       public  7200
...

````

#### key:criterion

#### VAR:condition


