---
authors: [davor]
categories:
  - FastStream
date: 2023-10-10
---

# How we deprecated two successful projects and joined forces to create an even more successful one

We had two large clients requesting to integrate our ML pipelines with their backend using Apache Kafka. Our previous HTTP API was based on FastAPI and we thought no problem, let's search for something similar but for Kafka. It turns out the one available solution was Faust, a framework with the last release at the time more than two years old. There is a community-maintained fork of it, but it was not very active and we just couldn't use it in an enterprise-level deployment.

<!-- more -->

After a short discussion, we concluded we were just too spoiled to use low-level libraries that were nothing more than just tiny wrappers around C++ libs and that we could just build our own. So, we shamelessly made one by reusing beloved paradigms from FastAPI and we shamelessly named it **[FastKafka](https://github.com/airtai/fastkafka)**. The point was to set the expectations right - you get pretty much what you would expect: function decorators for consumers and producers with type hints specifying Pydantic classes for JSON encoding/decoding, automatic message routing to Kafka brokers and documentation generation.

After deploying it with our clients, we decided to open-source it just to see if there was any interest in something like this. We made a post about it on the Hacker news and the thing just took off overnight! I remember posting it in the evening and looking into an overnight (literally) success: there were the first 50 stars in a few hours. Five days later, we crossed the 200 stars and then the HN post started to wear off and growth slowed down.

![FastKafka's Star History Graph](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/3ohe2o1n81gcfkkxh4e6.jpeg "FastKafka's Star History Graph")

The next step was to figure out what to do next. We posted questions on a few relevant subreddits and got quite a few feature requests, mostly around supporting other protocols, encoding schemas etc. But, we also got a message from a developer of a similar framework **[Propan](https://github.com/Lancetnik/Propan)** that was released at about the same time and was gaining quite a traction in the RabbitMQ community. That developer was **[Nikita Pastukhov](https://github.com/Lancetnik)** and he made an intriguing proposal: **let's join our efforts and create one framework with the best features of both**. Both projects were growing at roughly the same speed but targeted different communities. So the potential for double growth was there. After a quick consideration, we realized there was not much to lose and there was a lot to gain. Of course, we would lose absolute control over the project but losing control to the community is the only way for an open-source project to succeed. On the positive side, we would gain a very skilled maintainer who single-handedly created a similar framework all by himself. The frameworks were conceptually very similar so we concluded there would not be much friction of ideas and we should be able to reach consensus on the most important design issues.

However, as developers, we test our hypothesis early to avoid failing later. So we started with creating a design document where we specified the main features and started discussing high-level API. There was no discussion on the implementation at all, just on what should be the look and feel of the framework to the end user. The process took roughly one month and after reaching a consensus on the design, we started the work on the implementation. The self-imposed deadline was mid-September because we already had two conference talks coming up and we wanted to use those opportunities to launch a new version.

After two months of hard work, we presented the newly released **[FastStream](https://github.com/airtai/faststream)** framework at **[Infobip Shift](https://shift.infobip.com/)** conference and got featured at **[ShiftMag](https://shiftmag.dev/fast-stream-python-framework-1646/)**. The framework now supports both Apache Kafka and RabbitMQ, but also NATS protocol with the plan to add more protocols in the near future. The overall code is much cleaner and the implementation is streamlined with abstractions covering the common functionality across the protocols. We deprecated both FastKafka and Propan, but promised to fix bugs as long as needed. However, it seems like the community already decided to switch over to gain new functionalities.

**A few posts on Reddit later and the community feedback is fantastic. We have never before experienced such growth and we are just 50 stars short from our goal of 1000, less than four week from the launch. I have no doubt that this was the right move and that collaboration and not competition is the right way to build long-term success in the open-source world.**

![FastStream's Star History Graph](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/bg4hqkoteqwaupxt3r77.png "FastStream's Star History Graph")
