# Deploying AgroVision AI — clean start (ECS Express Mode + Vercel)

App Runner is closed to new customers (April 2026), so this uses AWS's
recommended replacement, **ECS Express Mode**, for the backend, and **Vercel**
for the frontend (already set up). Everything AWS-side runs in **AWS
CloudShell** — the terminal built into your AWS Console — so nothing needs
installing on your laptop.

End state: a live backend URL (ECS/ALB) + a live frontend URL (Vercel),
talking to each other.

---

## Part A — Push your code to GitHub (if not already done)

On your own machine:

```bash
cd agrovision_final2
git init
git add -A
git commit -m "First Commit"
```
Create an empty repo at https://github.com/new (no README), then:
```bash
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```
If you already have a repo, just make sure `backend/Dockerfile` is committed and pushed — it's new.

---

## Part B — Open AWS CloudShell

AWS Console → click the CloudShell icon (`>_`) in the top nav bar, or bottom-left where you've seen it before.
Wait ~30 seconds for it to boot. Everything from here runs inside this terminal.

---

## Part C — Deploy the foundation stack (S3 bucket, ECR repo, IAM role)

In CloudShell:

```bash
git clone https://github.com/<you>/<repo>.git
cd <repo>/infra

aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name agrovision-foundation \
  --parameter-overrides ProjectName=agrovision \
  --capabilities CAPABILITY_NAMED_IAM

aws cloudformation describe-stacks \
  --stack-name agrovision-foundation \
  --query "Stacks[0].Outputs" --output table
```

Copy the 3 output values — you'll need all of them below:
- `BackendRepoUri`
- `AppBucketName`
- `EcsTaskRoleArn`

---

## Part D — Upload model weights to S3

Still in CloudShell:

```bash
cd ../backend
APP_BUCKET=<paste AppBucketName>

for f in best_model.keras class_names.json recommend_model.pkl yield_model.pkl \
         decision_model.pkl fusion_model.pkl geo_model.pkl geo_spread_model.pkl \
         outbreak_model.pkl rl_model.pkl soil_model.pkl progression_model.pkl \
         feedback_model.pkl; do
  aws s3 cp "models/$f" "s3://$APP_BUCKET/models/$f"
done
```
(If `models/` isn't in your GitHub repo because it's gitignored — correct, it
shouldn't be — upload these from your local machine instead using the AWS CLI,
or `aws s3 cp` one at a time via the S3 console's upload button.)

---

## Part E — Build and push the Docker image

Still in `backend/`, in CloudShell:

```bash
REPO_URI=<paste BackendRepoUri>
REGION=<your region, e.g. ap-south-1>

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $(echo $REPO_URI | cut -d'/' -f1)

docker build -t agrovision-backend .
docker tag agrovision-backend:latest $REPO_URI:latest
docker push $REPO_URI:latest
```
This takes a few minutes (installing TensorFlow etc. inside the image).

---

## Part F — Create the ECS Express Mode service (console)

AWS Console → search **"ECS"** → Elastic Container Service → left nav → **Express Mode** → **Create**.

- **Image URI**: `<BackendRepoUri>:latest`
- **Container port**: `8080`
- **Health check path**: `/health`
- **Task execution role**: click "Create new role" (one-time, auto-configured)
- **Task role**: select the existing role — `agrovision-ecs-task-role` (this is `EcsTaskRoleArn` from Part C)
- **Infrastructure role**: click "Create new role" (one-time)
- CPU/Memory: **1 vCPU / 2 GB** minimum (TensorFlow needs the room)
- **Environment variables**:
  ```
  STORAGE_BACKEND=s3
  S3_DATA_BUCKET=<AppBucketName>
  S3_UPLOADS_BUCKET=<AppBucketName>
  MODELS_S3_BUCKET=<AppBucketName>
  AWS_REGION=<your region>
  ENABLE_AUTO_RETRAIN=false
  GEMINI_API_KEY=<your key>
  OPENWEATHER_API_KEY=<your key>
  GOOGLE_PLACES_API_KEY=<your key>
  ```
- Click **Create**.

Wait for the deployment to finish (Resources tab shows progress — a few minutes).
Copy the **Application URL** shown on the service page once it's done — something like:
```
http://agrovision-backend-xxxx.<region>.elb.amazonaws.com
```

**Verify it:**
```bash
curl <Application URL>/health
# expect: {"status": "ok"}
```

---

## Part G — Point the frontend at it

Vercel dashboard → your project → **Settings → Environment Variables**:
```
VITE_API_URL = <Application URL from Part F>
```
(no trailing slash)

**Deployments** → latest → **⋯ → Redeploy** (must be a fresh build — Vite bakes env vars in at build time).

Confirm `frontend/vercel.json` is committed with:
```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
```
(fixes client-side routes like `/scan` 404ing on refresh)

---

## Part H — Test end to end

1. Open your Vercel URL
2. Sign up / log in
3. Upload a leaf photo, run a scan
4. Confirm a result comes back and the dashboard shows it after a refresh (proves S3-backed storage is working)

That's your submission: the Vercel URL as the live site, backed by a real AWS deployment (ECS Fargate + S3 + ECR).

---

## Re-deploying after changes

- **Backend code changed**: repeat Part E (`docker build` → `docker tag` → `docker push`), then in the ECS console click **Update service** on your Express Mode service and hit deploy again.
- **Frontend changed**: just push to GitHub — Vercel auto-redeploys.
