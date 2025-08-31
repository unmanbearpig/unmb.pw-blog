build:
	bash --login -c "chruby-init; bundle exec jekyll build"

serve:
	bash --login -c "chruby-init; bundle exec jekyll serve"
run: serve

deploy: build
	./_deploy.sh
