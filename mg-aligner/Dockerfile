FROM ubuntu:latest

RUN apt-get update && apt-get install -y gcc g++ make zlib1g-dev

ADD . /src
WORKDIR /src
RUN make all

FROM ubuntu:latest
COPY --from=0 /src/bwbble /usr/bin/bwbble
ADD entrypoint.sh /usr/bin/entrypoint.sh

RUN chmod +x /usr/bin/entrypoint.sh
RUN apt-get update && apt-get install -y libgomp1

WORKDIR /
ENTRYPOINT ["/usr/bin/entrypoint.sh"]
CMD []