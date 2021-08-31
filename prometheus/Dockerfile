FROM golang:1.14 AS gobuild

ENV PATH=$PATH:/opt/go/bin

# Copy our source into WORKDIR
WORKDIR /gobuild
COPY . .

# Run golang build.
RUN go build -o remote-storage-adapter main.go

FROM gcr.io/distroless/base

WORKDIR /dem

COPY --from=gobuild /gobuild/remote-storage-adapter /dem/remote-storage-adapter

# Exposes port 9201 to the outside world
EXPOSE 9201

ENTRYPOINT ["/dem/remote-storage-adapter"]
