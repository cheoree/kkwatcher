if [ ! -f .env ]; then
  echo ".env file not found. Copy .env.example to .env and fill values."
  exit 1
fi

set -a
. ./.env
set +a

pkill -f python
#nohup python3 kkwatcher.py &> kk.log &
#nohup python3 sjwatcher.py &> sj.log &
#nohup python3 dgwatcher.py &> dg.log &
#nohup python3 bmwatcher.py &> bm.log &
