
import shutil
import os
import logging

# Setup basic logging
logging.basicConfig(filename='game_debug.log', level=logging.DEBUG, filemode='w')

def cleanup():
    logging.info("Starting cleanup...")
    try:
        if os.path.exists('__pycache__'):
            shutil.rmtree('__pycache__')
            logging.info("Removed __pycache__ directory.")
        
        # Also walk and remove nested __pycache__
        for root, dirs, files in os.walk('.'):
            if '__pycache__' in dirs:
                shutil.rmtree(os.path.join(root, '__pycache__'))
                logging.info(f"Removed nested __pycache__ in {root}")
                
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")

if __name__ == "__main__":
    cleanup()
    print("Cleanup complete.")
