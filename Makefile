build:
	bundle exec jekyll build

serve:
	bundle exec jekyll serve
run: serve

deploy: build
	./_deploy.sh
