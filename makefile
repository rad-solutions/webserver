test:
	# python manage.py test
	docker compose exec web python manage.py test

down:
	docker-compose down

docker-migrate-create-admin:
	docker-compose exec web sh -c "python manage.py makemigrations && python manage.py migrate"
	docker-compose exec web python manage.py shell -c "import app.scripts.create_users; app.scripts.create_users.run()"
	@echo "Superusuario 'admin' creado con contraseña 'admin' y correo 'admin@gmail.com'"
	@echo "Usuario cliente 'cliente' creado con contraseña 'clientepass' y rol 'Cliente'"

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
