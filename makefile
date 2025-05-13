test:
	docker compose exec web poetry run pytest

down:
	docker compose down

docker-migrate-create-admin:
	docker compose exec web sh -c "poetry run python manage.py makemigrations && poetry run python manage.py migrate"
	docker compose exec web poetry run python manage.py shell -c "from app.scripts import create_users; create_users.run()"
	@echo "Superusuario 'admin' creado con contraseña 'admin' y correo 'admin@gmail.com'"
	@echo "Usuario cliente 'cliente' creado con contraseña 'clientepass' y rol 'Cliente'"

setup:
	docker compose up -d --build
	make docker-migrate-create-admin
	@echo "Sistema iniciado y configurado correctamente."

lint:
	poetry run flake8 .
	poetry run isort . --check --profile black

format:
	poetry run black .
	poetry run isort .
	poetry run flake8 .

precommit:
	poetry run pre-commit run --all-files
