all: build
build: build-client
push: push-client
.PHONY: push build


TAG_CLIENT = 1.0.6
PROJECT_NAME = context_query_results

build-client:
	docker build -t projectepic/$(PROJECT_NAME) .
	docker tag projectepic/$(PROJECT_NAME) projectepic/$(PROJECT_NAME):$(TAG_CLIENT)

push-client: build-client
	docker push projectepic/$(PROJECT_NAME)
	docker push projectepic/$(PROJECT_NAME):$(TAG_CLIENT)

clean:
	docker rmi projectepic/$(PROJECT_NAME):$(TAG) || :
	docker rmi projectepic/$(PROJECT_NAME) || : 
