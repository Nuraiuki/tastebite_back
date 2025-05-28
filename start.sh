# start.sh
flask --app app db upgrade   # apply pending migrations
gunicorn -b 0.0.0.0:$PORT 'app:create_app()'
