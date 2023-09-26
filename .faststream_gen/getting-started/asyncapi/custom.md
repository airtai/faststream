# Customizing AsyncAPI Documentation for FastStream

In this guide, we will explore how to customize AsyncAPI documentation for your FastStream application. Whether you want to add custom app info, broker information, handlers, or fine-tune payload details, we'll walk you through each step.

## Prerequisites

Before we dive into customization, ensure you have a basic FastStream application up and running. If you haven't done that yet, follow the FastStream documentation to set up a simple app.

## Setup Custom FastStream App Info

Let's start by customizing the app information that appears in your AsyncAPI documentation. This is a great way to give your documentation a personal touch. Here's how:

- [x] Locate the app configuration in your FastStream application.
- [x] Update the `title`, `version`, and `description` fields to reflect your application's details.
- [x] Save the changes.
- [x] Serve your FastStream app.

Now, your documentation reflects your application's identity and purpose.

## Setup Custom Broker Information

The next step is to customize broker information. This helps users understand the messaging system your application uses. Follow these steps:

- [x] Locate the broker configuration in your FastStream application.
- [x] Update the `name`, `description`, and other relevant fields.
- [x] Save the changes.
- [x] Serve your FastStream app.

Your AsyncAPI documentation now provides clear insights into the messaging infrastructure you're using.

## Setup Custom Handler Information

Customizing handler information helps users comprehend the purpose and behavior of each message handler. Here's how to do it:

- [x] Navigate to your handler definitions in your FastStream application.
- [x] Add descriptions and summary information to each handler using comments or annotations.
- [x] Save the changes.
- [x] Serve your FastStream app.

Now, your documentation is enriched with meaningful details about each message handler.

## Setup Payload Information via Pydantic Model

To describe your message payload effectively, you can use Pydantic models. Here's how:

- [x] Define Pydantic models for your message payloads.
- [x] Annotate these models with descriptions and examples.
- [x] Use these models as arguments or return types in your handlers.
- [x] Save the changes.
- [x] Serve your FastStream app.

Your AsyncAPI documentation now showcases well-structured payload information.

## Generate Schema.json, Customize Manually, and Serve It

To take customization to the next level, you can manually modify the schema.json file. Follow these steps:

- [x] Generate the initial schema.json using FastStream's built-in tools.
- [x] Manually edit the schema.json file to add custom fields, descriptions, and details.
- [x] Save your changes.
- [x] Serve your FastStream app with the updated schema.json.

Now, you have fine-tuned control over your AsyncAPI documentation.

## Conclusion

Customizing AsyncAPI documentation for your FastStream application not only enhances its appearance but also provides valuable insights to users. With these steps, you can create documentation that's not only informative but also uniquely yours.

Happy coding with your customized FastStream AsyncAPI documentation!
