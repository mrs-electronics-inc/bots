## RC Process for Docker Image Changes

When working on changes to Docker-based bots (e.g., code-review-bot):

1. Make code changes on the feature branch and commit
2. Tag an RC (e.g., `v0.14.0-rc1`) and push the tag
3. Wait for the Publish Bot Images workflow to complete
4. Update the workflow that references the image to the new tag
5. Push the workflow change to trigger a test run
6. Watch the run, download artifacts, analyze output
7. Fix issues and repeat from step 1

Never push the workflow bump until the image is built.
