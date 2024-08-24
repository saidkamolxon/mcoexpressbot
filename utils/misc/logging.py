import logging

logging.basicConfig(filename='app.log',
                    filemode='a',
                    format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)
