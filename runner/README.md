# README
Run checkov in a container


## example:
```bash
git clone <this repo>
docker build -t tmp/ckv .
docker run --rm tmp/ckv -f s3.tf

```

*use exit codes*:
```bash
docker run --tmp/ckv --version ; echo $?
3.2.50
0

docker run --tmp/ckv s3.tf ; echo $?
...
1
```
