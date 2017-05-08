# http_proxy
A simple HTTP proxy that supports byteranges for hosts that do not.

Running (assumes you have docker-compose already installed)
=======
Start the application container:

  ```
  docker-compose up
  ```

Use the proxy on the Linux command-line like this:

  ```
  http_proxy=localhost:8080 curl http://www.msn.com
  ```

or by setting up your browser to use the HTTP proxy.


Use the proxy on the Linux command-line with a byterange like this:

  ```
  http_proxy=localhost:8080 curl http://www.msn.com?range=bytes=1-10
  ```

or

  ```
  http_proxy=localhost:8080 curl http://www.msn.com -H 'Range: bytes=1-10'
  ```

You can also use the proxy remotely by using the docker container's IP address which you can find vi:

  ```
  docker-compose run web ip addr
  ```

To see the proxy stats go to ```http://<container-ip>:8080/stats```
