# tech-dict


## Development

1. Ask an owner of this project for an account on the [Contentful](https://www.contentful.com) project.

2. You'll need to create a new API key to fetch the content from the Contentful CMS. In Contentful, go to the Settings page and then API Keys. Click `Add API Key`. Name it something useful.

3. Copy the environment variable file and paste in your the `Content Delivery API access token`.

```bash
cp env_example.sh env.sh

# edit env.sh to have your API token

# set your environment variables
source env.sh
```

4. Install requiremnts
```
pip install -r requirements.txt
```

5. Run
```
make run
```

You can see the site at http://127.0.0.1:5000

```
# Install firebase cli
https://firebase.google.com/docs/cli#install_the_firebase_cli
```
