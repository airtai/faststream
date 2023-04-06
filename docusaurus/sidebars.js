module.exports = {
    tutorialSidebar: [
        'index',
        {
            "Guides": ['guides/Guide_04_Github_Actions_Workflow', 'guides/Guide_30_Using_docker_to_deploy_fastkafka', 'guides/Guide_31_Using_redpanda_to_test_fastkafka', {
                'Consuming from Kafka': ['guides/Guide_11_Consumes_Basics']
            }, {
                'Producing to Kafka': ['guides/Guide_21_Produces_Basics', 'guides/Guide_22_Partition_Keys']
            }]
        },
//         [require("./docs/reference/sidebar.json")],
        {
            "items": [
                "api/fastkafka/FastKafka",
                "api/fastkafka/KafkaEvent",
                {
                  "items": [
                    "api/fastkafka/testing/ApacheKafkaBroker",
                    "api/fastkafka/testing/LocalRedpandaBroker",
                    "api/fastkafka/testing/Tester"
                  ],
                  "label": "testing",
                  "type": "category"
                },
            ],
            "label": "API",
            "type": "category"
        },
        {
            "CLI": ['cli/fastkafka', 'cli/run_fastkafka_server_process'],
        },

        "CHANGELOG",
    ],
};