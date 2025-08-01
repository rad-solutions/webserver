test:
	docker compose exec web poetry run python manage.py test app.tests

down:
	docker compose down

docker-migrate-create-admin:
	docker compose exec web sh -c "poetry run python manage.py makemigrations && poetry run python manage.py migrate"
	docker compose exec web poetry run python manage.py shell -c "from app.scripts import create_users; create_users.run()"

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

populate-db:
	docker compose exec web poetry run python manage.py populate_db
	@echo "Base de datos poblada con datos sintéticos."

pagination-test-populate-db:
	docker compose exec web poetry run python manage.py populate_data
	@echo "Base de datos poblada con datos sintéticos para pruebas de paginación."
