build:
	docker build -t victorvsm/blog_app:last .
	docker push victorvsm/blog_app:last

start:
	docker-compose up -d --build

stop:
	docker-compose down