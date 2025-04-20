# 🛠️ Secure, Scalable, and Performant Static Website on AWS With Scalable Notification system and Push Notifications

## 📚 Overview
This project implements a fully serverless and secure static web application infrastructure using AWS services. The primary goals are performance, scalability, security, and cost-effectiveness. The frontend is built with HTML, CSS, and JavaScript and is deployed on AWS S3. The backend is a FastAPI application deployed on AWS Lambda. The entire system is integrated and protected with security services like AWS WAF and CloudFront, monitored using CloudWatch, and documented for future teams or audits.

All AWS Lambda functions are deployed and managed using **GitHub Actions** to enable a seamless CI/CD pipeline.

### 🧠 Lambda Functions Used
- **FastAPI Lambda (API Gateway Integration)**: Serves the main backend API for authentication, posts, votes, and user preferences.
- **vote-processor-lambda**:
  - Triggered via SQS queue.
  - Processes vote events (like/dislike).
  - Sends email notifications using SES.
  - Sends SMS using SNS.
  - Notifies via Slack/webhook integrations.
- **milestone-lambda**:
  - Triggered via **Amazon EventBridge** on custom schedule or event patterns.
  - Sends milestone alerts and promotional messages.
  - Used for re-engagement and marketing workflows.

---

## ✅ Step 1: Set up an S3 Bucket to Store Website Files
### 🏗️ Implementation
- Created an S3 bucket with a unique name (e.g., `myapp-frontend-bucket`).
- Configured the bucket for static website hosting:
  - Enabled static website hosting.
  - Set `index.html` as the index document and `error.html` as the error document.
- Uploaded static files:
  - `index.html`: main landing page.
  - `main.js`: handles authentication, post interaction, push notification registration, etc.
  - `style.css`: basic styling.
  - `sw.js`: service worker file to handle web push notifications and background sync.
- Made the files publicly accessible by adding a bucket policy (temporarily, until CloudFront was added for security).

### 🔔 Service Worker Details
- Created a `sw.js` file responsible for push notifications:
  - Listens for `push` events and displays notifications using the Notification API.
  - Can also handle background sync and offline caching if extended.
- Registered in `main.js`:
  ```javascript
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('Service Worker registered:', reg))
      .catch(err => console.error('SW registration failed:', err));
  }
  ```
- Ensured S3 correctly serves `.js`, `.json`, and `.webmanifest` files with appropriate MIME types via metadata.

### 🔐 Security
- Disabled public access once CloudFront was in place.
- Enabled server-side encryption with Amazon S3-managed keys (SSE-S3).

---

## ✅ Step 2: Configure CloudFront for Global CDN
### 🌍 Implementation
- Created a CloudFront distribution:
  - Origin: the S3 bucket endpoint.
  - Default root object: `index.html`.
  - Enabled caching for faster load times.
  - Redirected HTTP to HTTPS.
  - Restricted bucket access via an Origin Access Control (OAC).
- Updated the S3 bucket policy to allow only CloudFront access via OAC.

### ⚡ Benefits
- Global edge locations ensure fast, reliable content delivery.
- Access to the S3 bucket is now fully private behind CloudFront.

---

## ✅ Step 3: Set Up AWS Certificate Manager for HTTPS
### 🔒 Implementation
- Requested a public SSL certificate via AWS Certificate Manager (ACM).
  - Used domain like `www.example.com` (replace with actual domain).
  - Verified via DNS using Route 53.
- Attached certificate to the CloudFront distribution.
- Enabled redirect from HTTP → HTTPS.

### 🌐 Result
- The entire website is now served securely via HTTPS worldwide.

---

## ✅ Step 4: Implement WAF to Block Malicious Traffic
### 🛡️ Implementation
- Created a Web ACL in AWS WAF with rules:
  - Rate limiting: Block IPs with >100 requests in 5 minutes.
  - Geo blocking: Block traffic from restricted countries (optional).
  - SQLi/XSS: Enabled AWS Managed Rules for SQL injection & XSS.
- Linked the Web ACL to the CloudFront distribution.

### ✅ Result
- Protection against common web exploits.
- Mitigates bot traffic, spamming, and malicious behavior.

---

## ✅ Step 5: Create CloudWatch Dashboards and Set Up Alerts
### 📊 Monitoring Setup
- Enabled CloudWatch metrics for:
  - **S3**: request count, latency, 4xx/5xx errors.
  - **CloudFront**: cache hit/miss, request volume, status codes.
  - **Lambda**: invocations, errors, durations.
- Built a custom CloudWatch dashboard showing all key metrics.
- Configured CloudWatch Alarms:
  - 5xx errors in CloudFront > 5 in 5 min → triggers SNS alert.
  - Lambda latency > 3s average over 5 min → triggers SNS alert.

### 🔔 Outcome
- Real-time observability and proactive failure alerts.

---

## ✅ Step 7: Project Summary & Business Impact
### 📌 Summary
This project provides a fast, secure, and auto-scaling web application using 100% managed AWS services. The use of service workers enables native push notification support, while CloudFront ensures low-latency global access. S3 offers reliable and inexpensive storage with strong security. The stack is serverless, cost-efficient, and easy to maintain.

The backend API is built with FastAPI and deployed on **AWS Lambda** behind an **API Gateway**. All Lambda function deployments are automated using **GitHub Actions** for continuous integration and delivery.

Additionally:

- A separate `vote-processor-lambda` asynchronously handles SQS messages for likes/dislikes:
  - Sends email notifications to post owners via SES.
  - Sends SMS alerts via SNS.
  - Posts to Slack channels or webhooks.

- A `milestone-lambda` is triggered by **EventBridge** rules:
  - Sends promotional or milestone-based alerts to users.
  - Can be extended to handle user engagement campaigns.

This architecture decouples core interactions (likes/votes) from long-running tasks, ensuring speed and reliability of user-facing APIs.

### 💼 Business Impact
- 🚀 **Performance**: Ultra-low latency via CloudFront and Lambda.
- 🛡️ **Security**: HTTPS, WAF, IAM-controlled access, Lambda isolation.
- 💰 **Cost-Effective**: Utilizes AWS Free Tier and pay-per-use.
- 🧘 **No Maintenance**: Fully managed & serverless.
- ⚖️ **Scalable**: Scales instantly with user demand.



