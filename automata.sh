for j in 16 32 64 128 256 512 1024
do
    for i in 1 2 3 4 5
    do 
        ./client.py "152.7.98.145" "7735" "sample.txt" $j 500 
    done
done