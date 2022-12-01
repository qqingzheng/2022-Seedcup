rm bot.out log_* logfile_* server.out client.out
find . | grep -E '\_\_pycache\_\_$' | xargs rm -r