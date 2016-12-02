import flask
app = flask.Flask(__name__)

import hashlib
import hmac
import logging
import subprocess

_logger = logging.getLogger(__name__)

@app.route('/github-webhook', methods=['POST'])
def github_webhook():
	secret = _get_secret('/etc/github-www.momoloji.org-webhook-secret')

	event = flask.request.headers['X-Github-Event']
	if event == 'push':
		_logger.info("Push event received")

		(alg, signature) = flask.request.headers['X-Hub-Signature'].split('=', 1)
		data = flask.request.data
		checksum = hmac.new(secret, flask.request.data, hashlib.sha1).hexdigest()

		if hmac.compare_digest(signature, checksum):
			_logger.info("Event checksum matches")
			_update_repo('/srv/www.momoloji.org')
		else:
			_logger.warning("Event checksum does not match")

	return ''

def _get_secret(fn):
	with open(fn, 'rb') as f:
		secret = f.readline().strip()
	return secret

def _update_repo(path):
	subprocess.run(['git', '-C', path, 'fetch'], check=True)
	subprocess.run(['git', '-C', path, 'reset', '--hard', 'origin/master'], check=True)
	subprocess.run(['git', '-C', path, 'clean', '-d', '-x', '-f'], check=True)
	subprocess.run(['killall', '-HUP', 'uwsgi'], check=True)
