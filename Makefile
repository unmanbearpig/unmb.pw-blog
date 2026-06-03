build:
	chruby-run bundle exec jekyll build

serve:
	chruby-run bundle exec jekyll serve
run: serve

deploy: build
	./deploy.sh
