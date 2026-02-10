build:
	bash --login -c "chruby-init; bundle exec jekyll build"

serve:
	bash --login -c "chruby-init; bundle exec jekyll serve"
run: serve

deploy: build
	rsync -avz  _site/ unmb.pw:/var/www/htdocs/unmb.pw/
	# ./_deploy.sh
