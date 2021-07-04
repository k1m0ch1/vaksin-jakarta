# vaksin api jakarta

because API service vaksinasi-corona.jakarta.go.id is sometime laggy, I made mirror API

I deploy this at `https://vaksin-jakarta.yggdrasil.id/`

data is included the vaccine location include with the schedule same with this https://twitter.com/mathdroid/status/1411712464916414467

# requirements
pip
pipenv
pm2

# install
1. pipenv instyall --deploy --system

## to run scrape for every 5 minutes
`pm2 start ./scrape.py --interpreter python3 --cron "*/5 * * * *" --name scrape-vaksin-jakarta --watch`

## to run the web server
`pm2 start ./main.py --interpreter python3 --name vaksin-api`