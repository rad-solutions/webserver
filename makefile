test:
	python manage.py test

down:
	docker-compose down

docker-migrate-create-admin:
	docker-compose exec web sh -c "python manage.py makemigrations && python manage.py migrate"
	docker-compose exec web sh -c "echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@gmail.com', 'admin') if not User.objects.filter(username='admin').exists() else None\" | python manage.py shell"
	@echo "Superusuario 'admin' creado con contraseña 'admin' y correo 'admin@gmail.com'"

setup:
	docker-compose up -d
	make docker-migrate-create-admin
	@echo "Sistema iniciado y configurado correctamente."

lint:
	flake8 .
	isort . --check --profile black

format:
	black .
	isort .
	flake8 .

precommit:
	pre-commit run --all-files
