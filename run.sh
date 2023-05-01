pkill -f python
nohup python3 kkwatcher.py &> kk.log &
nohup python3 sjwatcher.py &> sj.log &
nohup python3 dgwatcher.py &> dg.log &
