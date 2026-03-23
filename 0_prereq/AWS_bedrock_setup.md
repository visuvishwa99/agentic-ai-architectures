# Amazon Bedrock Agents -- Integrated Master Guide (2026)

**Principles + AgentCore Architecture. Every prerequisite. Every step in order.**

---

## Before You Begin: Account Prerequisites

You need these in place before starting Phase 1. If you already have them, skip ahead.

### Prerequisite A -- Create an IAM Admin User

If you're on a brand new AWS account, you're logged in as root. The budget killswitch (Phase 1, Step 4) needs a specific IAM user to target -- it cannot target root. You also should not use root for daily work.

1. Log in to the **AWS Management Console** as the root user.
2. In the top search bar, type **"IAM"** and open the IAM service.
3. Click **Users** > **Create user**.
4. **User name:** `bedrock-admin`
5. Check **Provide user access to the AWS Management Console**.
6. Choose **I want to create an IAM user** (not Identity Center).
7. Set a **Custom password** or let AWS auto-generate one.
8. Uncheck "User must create a new password at next sign-in" if you want to keep the password you set.
9. Click **Next**.
10. Select **Attach policies directly**.
11. Search for `AdministratorAccess` and check the box.
12. Click **Next** > **Create user**.
13. **Save these now:**
    - The **Console sign-in URL** (e.g., `https://123456789012.signin.aws.amazon.com/console`)
    - The **Username** and **Password**
14. **Sign out** of root.
15. **Sign back in** using the sign-in URL with your `bedrock-admin` credentials.

> **From this point forward, do everything as `bedrock-admin`.**

> **What just happened:** You created a separate IAM user so you're not using the all-powerful root account for daily work. This user has full admin access but, critically, it can be targeted by IAM policies -- which is how the budget killswitch will lock out Bedrock access if your spend hits the limit. Root cannot be targeted this way, which is why this step is required.

---

### Prerequisite B -- Choose Your AWS Region

Bedrock and specific models are not available in every region. Set this once and don't change it.

1. In the **top-right corner** of the console, click the region dropdown.
2. Select **US East (N. Virginia) `us-east-1`** or **US West (Oregon) `us-west-2`**.
3. Confirm by searching **"Bedrock"** in the console -- the service should appear.

> **Switching regions later means starting over.** Pick one and stick with it.

> **What just happened:** You locked in your AWS region. Every service you configure from here (Bedrock, Lambda, CloudWatch, IAM policies) will live in this region. If you switch later, none of your existing resources will be visible in the new region.

---

### Prerequisite C -- Create the Budgets Action IAM Role

AWS Budgets needs its own role to attach policies on your behalf. Without this, the killswitch in Phase 1 cannot fire automatically.

1. Go to **IAM** > **Roles** > **Create role**.
2. **Trusted entity type:** AWS service.
3. **Use case:** Search for **Budgets** and select it.
4. Click **Next**.
5. Search for and check `AWSBudgetsActionsWithAWSResourceControlAccess`.
6. Click **Next**.
7. **Role name:** `AWS_Budgets_Action_Role`
8. Click **Create role**.

> **Checkpoint:** IAM > Roles > search `AWS_Budgets_Action_Role`. Confirm it exists.

> **What just happened:** You created a role that gives AWS Budgets permission to act on your behalf. When your budget threshold is hit, Budgets needs to "reach into" IAM and attach a Deny policy to your user. Without this role, Budgets has no authority to do that -- it would just send you an email and hope you notice.

---

## Phase 1: Budgetary "Killswitch" Setup

**Goal:** Prevent any unexpected cost spikes.

---

### Step 1 -- Create the Killswitch IAM Policy

This policy blocks all Bedrock access when applied. On its own it does nothing -- the budget triggers it.

1. Go to **IAM** > **Policies** > **Create policy**.
2. Click the **JSON** tab.
3. Delete everything and paste:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockKillswitch",
            "Effect": "Deny",
            "Action": "bedrock:*",
            "Resource": "*"
        }
    ]
}
```

4. Click **Next**.
5. **Policy name:** `Bedrock-Cost-Guardrail`
6. **Description:** `Denies all Bedrock access. Triggered by Budget Actions as a killswitch.`
7. Click **Create policy**.

> **Checkpoint:** IAM > Policies > filter "Customer managed." You should see `Bedrock-Cost-Guardrail` with "Used as" = None.

> **What just happened:** You created a "Deny all Bedrock" policy. Think of it like a fire extinguisher sitting on the wall -- it doesn't do anything until someone pulls it. The budget action (Step 3) is what "pulls" it by attaching this policy to your user when spend hits the limit.

---

### Step 2 -- Create the Zero-Spend Budget

This catches any spend the instant it happens -- even $0.01.

1. Search **"Budgets"** in the console and open it.
2. Click **Create budget**.
3. Choose **Use a template (simplified)**.
4. Select **Zero spend budget**.
5. Enter your **email address**.
6. Click **Create budget**.

> **What just happened:** You set a tripwire at $0.01. The moment AWS charges anything to your account -- even a fraction of a cent -- you get an email. This is your earliest possible warning that something is being billed.

---

### Step 3 -- Create the Custom $20 Budget (with Email Alerts)

This is your main project budget with progressive warnings.

1. Click **Create budget** again.
2. Choose **Customize (advanced)** > **Cost budget** > **Next**.
3. **Budget name:** `Bedrock-Project-Budget`
4. **Budgeted amount:** `$20.00`
5. Click **Next** to go to Alerts.
6. **Add Alert 1:**
   - Threshold: **50%** of actual spend ($10.00)
   - Email: your email
7. **Add Alert 2:**
   - Threshold: **80%** of actual spend ($16.00)
   - Email: your email
8. **Add Alert 3:**
   - Threshold: **100%** of actual spend ($20.00)
   - Email: your email
9. Click **Next** to go to **Actions**.
10. Click **Add Action** and configure:
    - **Select IAM role:** `AWS_Budgets_Action_Role` (from Prerequisite C)
    - **Which action type:** `IAM Policy`
    - **Select IAM policy:** `Bedrock-Cost-Guardrail` (from Step 1)
    - **Choose the user, group, or role to apply to:** Select `bedrock-admin` (from Prerequisite A)
    - **Run automatically?** Select **Yes**
11. Make sure this action is under the **100% actual spend** threshold.
12. Also add a **Forecasted Alert:**
    - Add another alert at **100% of forecasted spend** -- this catches high-velocity usage before it actually hits your $20 limit.
    - Email: your email
13. Click **Next** > Review > **Create budget**.

> **Phase 1 Complete.** You now have:
> - Instant notification at $0.01 (zero-spend budget)
> - Progressive email alerts at 50%, 80%, 100% actual + 100% forecasted
> - Automatic killswitch: `Bedrock-Cost-Guardrail` policy attaches to `bedrock-admin` at $20 actual spend, blocking all Bedrock access

---

## Phase 2: Bedrock Foundation & Model Choice

**Goal:** Access models and optimize for performance and cost.

---

### Step 1 -- Verify Model Access

As of 2026, the old "Model Access" page has been retired. Models auto-enable when first invoked.

1. Go to **Amazon Bedrock** > **Model catalog** (left sidebar).
2. Find **Claude 3.5 Sonnet** (Anthropic):
   - **For Anthropic models:** First-time users must **submit use case details**. Click the model and follow the prompts. This is a one-time step.
3. Find **Amazon Nova Micro**:
   - Nova models work **immediately** with no approval needed.
4. To confirm access, click any model > **Open in playground**. If it responds, you're good.

| Model | Purpose | Approx. Cost |
|---|---|---|
| **Amazon Nova Micro** | Cheap debugging & testing | ~$0.00006 / 1K tokens |
| **Claude 3.5 Sonnet** | Production -- high reasoning | Higher cost |
| **Claude 4.5 Sonnet** | Production -- if available in your region | Higher cost |

> **What just happened:** You confirmed which AI models your agent can use. Nova Micro is your cheap testing model (pennies per thousands of requests), and Claude is your production model (smarter but more expensive). For Anthropic models, you submitted your use case once -- you won't need to do this again.

---

### Step 2 -- Enable Provisioning / Model Selection Notes

When creating or editing your agent later (Phase 3), keep these in mind:

- **Uncheck "Bedrock Agents optimized"** in the model selection dropdown to see the full list of available models, including specific global inference profiles and newer versions like Claude 4.5 or 3.5.
- This setting is in the agent's Model selection area -- not a global toggle.

---

### Step 3 -- Prompt Caching

If your agent will have long system instructions or repeated context documents:

1. In the Bedrock console, check if **Prompt Caching** is available for your selected model.
2. Enable it when invoking the model (via API or agent configuration).
3. This can save **up to 90% on input token costs** for repeated prefixes.

> **Tip:** Always test with Nova Micro first. You can fail 100 times for less than a cent.

---

## Phase 3: Building the Agent (The "Anatomy")

**Goal:** Construct the "Brain" and the "Hands" of your system.

---

### Step 1 -- The Brain (LLM) -- Create and Configure the Agent

1. In the Bedrock console, go to **Agents** (left sidebar) > **Create Agent**.
2. **Agent name:** A clear name (e.g., `car-parts-assistant`).
3. **Agent description:** Its purpose (e.g., "Helps users find compatible car parts and check inventory").
4. **Agent resource role:** Select **"Create and use a new service role."**
   - AWS auto-generates a role like `AmazonBedrockExecutionRoleForAgents_XXXXXXXX` with Bedrock permissions.
   - If you prefer to use a manually created role, select "Use an existing service role" and pick your custom role.
5. **Model selection:**
   - Click the model dropdown.
   - **Uncheck "Bedrock Agents optimized"** to see all Claude versions.
   - Select **Claude 3.5 Sonnet** (or 4.5 if available).
6. **Agent instructions** (system prompt) -- this is the "role-based system prompt" that defines the agent's persona. Example:
   ```
   You are an automated logistics agent. Help users track shipments,
   find delivery estimates, and resolve shipping issues using the
   available tools. Always confirm the tracking number before
   searching.
   ```
7. **Additional settings:** Expand and enable **User Input** so the agent can ask clarifying questions.
8. Click **Save**.

> **What just happened:** You created the agent's "Brain." The model (Claude) is the intelligence, and the system prompt tells it who it is and how to behave. The agent can now have conversations, but it can't DO anything yet -- it has no tools. That's what Action Groups add next.

---

### Step 2 -- The Hands (Action Groups) -- Create Lambda + OpenAPI Schema + Link

Action Groups give the agent the ability to take action. The agent reads the OpenAPI schema to understand what tools it has, then calls your Lambda function when it decides to use one.

This step has 4 sub-steps: create the Lambda function, add a resource policy, create the OpenAPI schema, and link everything in the Action Group.

---

#### Step 2a -- Create the Lambda Function

The Lambda function contains the business logic the agent will execute. We'll start with a simple example that returns the current date and time -- you can replace this with your own logic later.

1. Open a new tab. Search for **"Lambda"** in the console and open it.
2. Click **Create function**.
3. Select **Author from scratch**.
4. **Function name:** `GetDateTimeFunction` (or whatever describes your function).
5. **Runtime:** Select **Python 3.12** (or your preferred Python version).
6. Leave everything else as default. Click **Create function**.
7. In the **Code** tab, **delete all existing code** and paste this:

```python
import json
import datetime

def lambda_handler(event, context):
    # Get current date and time
    now = datetime.datetime.now()
    response = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S")
    }

    # Format the response for Bedrock Agent
    response_body = {
        "application/json": {
            "body": json.dumps(response)
        }
    }

    action_response = {
        "actionGroup": event["actionGroup"],
        "apiPath": event["apiPath"],
        "httpMethod": event["httpMethod"],
        "httpStatusCode": 200,
        "responseBody": response_body,
    }

    session_attributes = event["sessionAttributes"]
    prompt_session_attributes = event["promptSessionAttributes"]

    return {
        "messageVersion": "1.0",
        "response": action_response,
        "sessionAttributes": session_attributes,
        "promptSessionAttributes": prompt_session_attributes,
    }
```

8. Click **Deploy** to save and deploy the function.
9. **Copy the Function ARN** from the top of the page (looks like `arn:aws:lambda:us-east-1:123456789012:function:GetDateTimeFunction`). Save it -- you need it in Step 2b.

> **Understanding the code:** Bedrock sends an event to your Lambda with fields like `actionGroup`, `apiPath`, and `httpMethod`. Your function does its work, then returns the result in a specific format that includes `messageVersion`, `response`, and session attributes. This exact format is required -- Bedrock won't understand the response otherwise.

---

#### Step 2b -- Add a Resource-Based Policy to the Lambda

Bedrock needs permission to invoke your Lambda function. You grant this with a resource-based policy.

1. In your Lambda function page, click the **Configuration** tab.
2. Click **Permissions** in the left sidebar.
3. Scroll down to **Resource-based policy statements** and click **Add permissions**.
4. Select **AWS service**.
5. **Service:** Select **Other**.
6. **Statement ID:** `AllowBedrockInvoke`
7. **Principal:** `bedrock.amazonaws.com`
8. **Source ARN:** `arn:aws:bedrock:REGION:ACCOUNT_ID:agent/*`
   - Replace `REGION` with your region (e.g., `us-east-1`)
   - Replace `ACCOUNT_ID` with your 12-digit AWS account ID (visible in top-right corner of console when you click your username)
   - The `/*` at the end means any Bedrock agent in your account can invoke this function
9. **Action:** Select `lambda:InvokeFunction`.
10. Click **Save**.

> **What just happened:** You gave Bedrock a "VIP pass" to call your Lambda function. Without this policy, Bedrock would try to invoke your Lambda and get an "Access Denied" error. The resource-based policy says "if the request comes from bedrock.amazonaws.com and it's from my AWS account, allow it."

---

#### Step 2c -- Create the OpenAPI Schema

The OpenAPI schema is a JSON file that tells the agent what your Lambda can do, what endpoints exist, and what parameters are needed. The agent reads this to decide when and how to call your function.

Create a file on your computer called `agent-api-schema.json` with this content:

```json
{
    "openapi": "3.0.0",
    "info": {
        "title": "DateTime API",
        "version": "1.0.0",
        "description": "API for getting the current date and time"
    },
    "paths": {
        "/getCurrentDateTime": {
            "get": {
                "summary": "Gets the current date and time",
                "description": "Returns the current date and time in UTC. Use this when the user asks what time or date it is.",
                "operationId": "getCurrentDateTime",
                "responses": {
                    "200": {
                        "description": "Successfully retrieved the current date and time",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "date": {
                                            "type": "string",
                                            "description": "The current date in YYYY-MM-DD format"
                                        },
                                        "time": {
                                            "type": "string",
                                            "description": "The current time in HH:MM:SS format"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
```

Save this file to your computer. You'll paste or upload it in the next step.

> **Key things about the schema:**
> - `openapi` must be `"3.0.0"` -- Bedrock requires this exact version.
> - `description` fields are critical -- the agent uses them to decide WHEN to call this API. Be as descriptive as possible.
> - `operationId` is required for every endpoint.
> - Each path (e.g., `/getCurrentDateTime`) maps to one action the agent can take.
> - When you build your real application later, you'll add more paths with parameters. For example, a `/getOrderStatus` endpoint might require an `orderId` parameter.

---

#### Step 2d -- Create the Action Group in Bedrock

Now link the Lambda function and OpenAPI schema to your agent.

**First, add Lambda permissions to the agent's role:**
1. Go to **IAM** > **Roles** > search for `AmazonBedrockExecutionRoleForAgents_` (the role AWS auto-created when you made the agent).
2. Click the role > **Add permissions** > **Attach policies**.
3. Search for `AWSLambdaRole` and attach it.

**Now create the Action Group:**
1. Go back to your agent in the **Bedrock console** (Agents > click your agent name).
2. Scroll to **Action Groups** > click **Add**.
3. **Action Group name:** `DateTimeActions` (or a name that describes what it does).
4. **Description:** `Gets the current date and time when a user asks.` (optional but recommended).
5. **Action group invocation:** Select **Select an existing Lambda function**.
6. **Lambda function:** Select `GetDateTimeFunction` (from Step 2a).
7. **Lambda function version:** Select `$LATEST`.
8. **Action group schema:** Select **Define with in-line OpenAPI schema editor**.
9. **Paste** the entire contents of your `agent-api-schema.json` file into the editor.
   - Alternatively: upload the JSON to an **S3 bucket** and select "Select an existing API schema" > browse to the S3 file.
10. Click **Create**.

> **What just happened:** Your agent now knows it has a tool called `getCurrentDateTime`. When a user asks "What time is it?", the agent will: (1) read the schema and decide this API is relevant, (2) invoke your Lambda function, (3) receive the date/time response, and (4) format a natural language answer for the user.

> **Quick-create alternative:** Bedrock also offers a **"Quick create a new Lambda function"** option in the Action Group setup. This auto-generates a basic Lambda skeleton that you edit later. Faster to start, but less control over the initial code.

> **Building your real application:** Replace the DateTime example with your actual business logic. For a car parts agent, you might have paths like `/getPartsByVehicle` (with `year`, `make`, `model` parameters) and `/checkInventory` (with a `partNumber` parameter). Each path maps to logic in your Lambda function, and you add more `if/elif` branches to handle each `apiPath`.

---

### Step 3 -- Memory (Context) -- Enable AgentCore Memory

AgentCore Memory allows the agent to remember context across interactions. This prevents redundant (and expensive) repeated calls.

1. In your agent's configuration page, scroll to **Memory** section.
2. Click **Add** (or **Create memory**).
3. **Memory name:** Leave the auto-generated name or give it a custom one.
4. **Short-term memory (raw event) expiration:** `90` days (default is fine).
5. Under **Long-term memory extraction strategies:**
   - Check **Summarization** -- this summarizes interactions to preserve critical context and key insights across sessions.
   - Leave the other strategies unchecked for now (Semantic memory, User preferences, Episodes). These are useful for advanced agents but not needed to start.
6. Leave the Strategy name and Namespace as their defaults.
7. Click **Create memory**.

> **What just happened:** You gave your agent a "notebook." Without memory, every conversation starts from zero -- the agent forgets the user's name, what they asked before, and what tools it already called. With Summarization enabled, the agent keeps condensed notes about each session, so it doesn't waste tokens re-asking the same questions or re-calling the same tools.

---

### Step 4 -- Guardrails -- Block PII and Harmful Content

Bedrock Guardrails add a safety layer on top of the model's reasoning, blocking PII, harmful content, or off-topic responses.

1. In the Bedrock console, go to **Guardrails** (left sidebar) > **Create guardrail**.
2. **Step 1 - Provide guardrail details:**
   - **Name:** `agent-safety-guardrail`
   - **Description:** `Content filters: Block harmful, violent, or sexual content. Denied topics: Define topics the agent should refuse to discuss. PII filters: Block or mask personally identifiable information.`
   - **Messaging for blocked prompts:** `Sorry, the model cannot answer this question.`
   - Check **Apply the same blocked message for responses**.
   - Leave Cross-Region inference, KMS, and Tags as defaults.
   - Click **Next**.
3. **Step 2 - Configure content filters:**
   - Enable filters for **Hate**, **Insults**, **Sexual**, **Violence**, and **Misconduct**.
   - Set the filter strength to **Medium** or **High** for each.
   - Click **Next**.
4. **Step 3 - Add denied topics:** Skip for now (click **Next**).
5. **Step 4 - Add word filters:** Skip for now (click **Next**).
6. **Step 5 - Add sensitive information filters:**
   - Under PII types, add: **SSN**, **Credit Card Number**, **Email**, **Phone Number**.
   - Set the action to **Block** or **Mask** for each.
   - Click **Next**.
7. **Step 6 - Contextual grounding check:** Skip for now (click **Next**).
8. **Step 7 - Automated Reasoning check:** Skip for now (click **Next**).
9. **Step 8 - Review and create:** Review your settings and click **Create guardrail**.

**Now attach it to your agent:**
1. Go back to your agent (Agents > click your agent name).
2. Scroll to **Guardrail details** > click **Edit**.
3. Select `agent-safety-guardrail` and choose the version (usually Version 1).
4. Click **Save**.

> **What just happened:** You added a safety net between your users and the model. Even if someone tries to trick your agent into revealing PII, generating harmful content, or going off-topic, the guardrail intercepts the request or response and blocks it. This works independently of the model's own safety features -- it's an extra layer that you control.

---

## Phase 4: Deploy, Observe, and Trace

**Goal:** Launch and verify the "Thought" process.

---

### Step 1 -- Prepare the Agent

**Saving is not enough.** You must also Prepare.

1. After all configuration changes, click **Save**.
2. Then click **Prepare** (top of the Agent Builder page).
   - Prepare deploys your configuration to the **AgentCore Runtime**.
   - Without Prepare, the test playground uses the **previous** version.

> **Rule: Every time you change anything -- Save, then Prepare.** Every single time.

> **What just happened:** You deployed your agent's configuration to the AgentCore Runtime. Think of "Save" as writing your changes to a draft, and "Prepare" as publishing that draft to production. If you only Save but don't Prepare, the test playground still runs the old version and you'll wonder why your changes aren't working.

---

### Step 2 -- Test with Trace

The Bedrock console has a built-in test window. Use the Trace to verify the agent's "thought process."

1. Click **Test** (top of the Agent Builder page) to open the test panel.
2. Type a test query (e.g., "What brake pads fit a 2019 Honda Civic?").
3. Click **Show Trace** on the response. Verify each stage:

| Trace Stage | What to Check |
|---|---|
| **Pre-processing** | Is the agent understanding the user's goal correctly? |
| **Orchestration** | Is it selecting the right tool (Lambda/Action Group)? Are the parameters correct? |
| **Post-processing** | Is the final response formatted correctly and useful? |

4. If something is wrong:
   - Adjust your instructions, OpenAPI schema, or Lambda logic.
   - **Save > Prepare > Test again.**
5. Repeat until the agent behaves correctly across multiple test queries.

> **Tip:** Show Trace is your primary debugging tool. Always check it when the agent gives unexpected answers.

> **What just happened:** You opened the hood of your agent and watched it think. The Trace shows every decision the agent makes: did it understand the question (Pre-processing), did it pick the right tool (Orchestration), and did it format the answer properly (Post-processing). If anything goes wrong in production, this is the first place you check.

---

### Step 3 -- CloudWatch Alarms (Token Burn Rate)

Catch infinite loops or runaway sessions before they drain your budget.

**Prerequisites:** Model invocation logging must be enabled in Bedrock Settings (you've already done this), and you must have made at least one test query so logs exist.

---

#### Step 3a -- Verify Logs Are Flowing

1. Search for **"CloudWatch"** in the top console search bar and open it.
2. In the left sidebar, click **Logs** > **Log groups**.
3. Click on your log group (e.g., `agent-first-log`).
4. You should see **Log streams** listed. Click on the most recent one.
5. Look for JSON log entries containing fields like `inputTokenCount` and `outputTokenCount`.
6. If you don't see any log streams, go back to your agent, run a test query (e.g., "What is the current date and time?"), wait 1-2 minutes, then refresh this page.

> **What just happened:** You confirmed that Bedrock is writing logs every time your agent processes a request. Each log entry contains the model used, the token counts (input and output), and request metadata. These logs are the raw data that powers your monitoring and alarms.

---

#### Step 3b -- Create a Metric Filter

A Metric Filter watches your logs for a specific field and turns it into a CloudWatch metric you can set an alarm on. This is a two-screen process: first you define the pattern, then you assign the metric.

**Screen 1 -- Define pattern:**

1. Go to **CloudWatch** > **Logs** > **Log groups**.
2. Click on your log group (e.g., `agent-first-log`).
3. Click **Actions** dropdown > select **Create metric filter**.
4. **Filter pattern** -- enter this exactly:
   ```
   { $.inputTokenCount > 0 }
   ```
   This matches any log entry that has an `inputTokenCount` field greater than 0.
5. (Optional) Under **Test pattern**, select a log stream and click **Test pattern** to verify it matches your existing log entries.
6. Click **Next**.

**Screen 2 -- Assign metric:**

7. **Filter name:** `BedrockInputTokenCount`
8. **Metric namespace:** `BedrockAgentMetrics`
   - Make sure **Create new** is selected (since this namespace doesn't exist yet).
9. **Metric name:** `InputTokenCount`
10. **Metric value:** `$.inputTokenCount`
    - This pulls the actual token count value from each log entry (not just a count of 1).
11. **Default value:** `0`
    - This ensures the metric always has data points, even when no logs match. Important for alarm state transitions.
12. **Unit:** Select **Count**.
13. Click **Next**.

**Screen 3 -- Review:**

14. Review all settings and click **Create metric filter**.

> **Checkpoint:** Go to your log group > click the **Metric filters** tab. You should see `BedrockInputTokenCount` listed. The metric won't show any data until new log events come in after the filter was created.

> **What just happened:** You built a translator between raw logs and CloudWatch metrics. Every time a new Bedrock log comes in with an `inputTokenCount` field, the filter extracts that number and publishes it as a metric called `InputTokenCount` in the `BedrockAgentMetrics` namespace. You can now graph this metric, set alarms on it, and track your token usage over time -- something you couldn't do with raw logs alone.

---

#### Step 3c -- Create the CloudWatch Alarm

Now create an alarm that fires when token usage spikes.

1. In **CloudWatch**, click **Alarms** > **All alarms** in the left sidebar.
2. Click **Create alarm**.
3. Click **Select metric**.
4. You'll see a screen with tiles like "Bedrock", "Lambda", "Logs", etc. and a search bar at the top.
5. In the **search bar** at the top, type `BedrockAgentMetrics` and press Enter.
   - If nothing appears, your metric filter hasn't received any data yet. Go to your Bedrock agent, run a test query (e.g., "What is the current date and time?"), wait 2-3 minutes, then come back and search again.
6. Click on **BedrockAgentMetrics** when it appears.
7. Click on **Metrics with no dimensions**.
8. Check the box next to **InputTokenCount**.
9. Click **Select metric**.
10. **Configure the alarm (Specify metric and conditions screen):**
    - **Statistic:** Select **Sum**.
    - **Period:** Select **5 minutes**.
    - Scroll down to **Conditions:**
    - **Threshold type:** Select **Static**.
    - **Whenever InputTokenCount is:** Select **Greater than**.
    - **than...:** Enter `50000` (50,000 tokens in 5 minutes indicates a likely infinite loop).
11. Click **Next**.
12. **Configure actions (Notification screen):**
    - **Alarm state trigger:** Select **In alarm**.
    - **Select an SNS topic:** Choose **Create new topic**.
    - **Create a new topic...:** Enter `bedrock-token-alert`
    - **Email endpoints that will receive the notification:** Enter your email address.
    - Click **Create topic**.
13. Click **Next**.
14. **Add name and description:**
    - **Alarm name:** `Bedrock-High-Token-Usage`
    - **Alarm description:** `Alerts when input token count exceeds 50,000 in 5 minutes, indicating a possible infinite loop.`
15. Click **Next** > Review all settings > Click **Create alarm**.
16. **IMPORTANT:** Check your email inbox and **click the confirmation link** in the email from AWS SNS. Without confirming, you will not receive alerts.

> **What this does:** If your agent consumes more than 50,000 input tokens in a 5-minute window (a strong sign of a logic loop or runaway session), you get an email alert. Combined with your budget killswitch from Phase 1, this gives you two layers of protection -- the alarm warns you early, and the killswitch cuts access at $20.

---

## Component Integration Summary

This table shows how each AgentCore component connects to your safety infrastructure:

| Component | Function | Alert Integration |
|---|---|---|
| **AgentCore Runtime** | Securely executes the agent | Monitored by CloudWatch Alarms |
| **AgentCore Gateway** | Connects to Lambda/APIs (Action Groups) | Budget Killswitch removes access at $20 |
| **AgentCore Memory** | Persists session state | Helps prevent redundant (expensive) calls |
| **AgentCore Identity** | Manages auth for tools | Ensures secure, governed access |
| **Bedrock Guardrails** | Blocks PII / harmful content | Safety layer on top of model reasoning |

---

## Pre-Deployment Checklist

### Prerequisites
- [ ] **IAM Admin User** -- `bedrock-admin` created, signed in (not root)
- [ ] **Region Set** -- `us-east-1` or `us-west-2`, consistent everywhere
- [ ] **Budgets Action Role** -- `AWS_Budgets_Action_Role` created

### Phase 1: Budgetary Killswitch
- [ ] **Killswitch Policy** -- `Bedrock-Cost-Guardrail` created in IAM
- [ ] **Zero-Spend Budget** -- $0.01 instant email notification
- [ ] **Custom Budget** -- `Bedrock-Project-Budget` at $20 with alerts at 50%, 80%, 100% actual + 100% forecasted
- [ ] **Budget Action Linked** -- Killswitch targets `bedrock-admin`, automatic execution enabled

### Phase 2: Bedrock Foundation
- [ ] **Model Access** -- Nova Micro working in Playground, Claude use case submitted
- [ ] **Model Selection Note** -- "Bedrock Agents optimized" unchecked for full model list
- [ ] **Prompt Caching** -- Enabled if using long system prompts

### Phase 3: Agent Anatomy
- [ ] **Brain (Agent)** -- Name, description, model, system prompt, User Input enabled
- [ ] **Agent Role** -- Auto-created or manual, with Lambda permissions attached
- [ ] **Lambda Function** -- Created, deployed, and resource-based policy added for Bedrock
- [ ] **OpenAPI Schema** -- JSON file created with descriptions for all endpoints
- [ ] **Agent Role Updated** -- `AWSLambdaRole` attached to agent's auto-created role
- [ ] **Action Group** -- Lambda + OpenAPI schema linked in agent config
- [ ] **Memory** -- Session summarization enabled
- [ ] **Guardrails** -- PII/content filters created and attached to agent

### Phase 4: Deploy & Observe
- [ ] **Saved and Prepared** -- Agent prepared after all config changes
- [ ] **Trace Tested** -- Pre-processing, Orchestration, Post-processing verified
- [ ] **CloudWatch Log Group** -- Created and receiving logs from Bedrock
- [ ] **Metric Filter** -- `BedrockInputTokenCount` filter on `inputTokenCount` field
- [ ] **CloudWatch Alarm** -- `Bedrock-High-Token-Usage` at 50K token threshold, SNS email confirmed
- [ ] **Tracing Enabled** -- Active for production debugging

---

*End of Guide*