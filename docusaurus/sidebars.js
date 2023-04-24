module.exports = {
tutorialSidebar: [
    'index', {'Guides': [{'Writing services': ['guides/Guide_11_Consumes_Basics', 'guides/Guide_21_Produces_Basics', 'guides/Guide_22_Partition_Keys', 'guides/Guide_05_Lifespan_Handler', 'guides/Guide_07_Encoding_and_Decoding_Messages_with_FastKafka']}, {'Testing': ['guides/Guide_31_Using_redpanda_to_test_fastkafka']}, {'Documentation generation': ['guides/Guide_04_Github_Actions_Workflow']}, {'Deployment': ['guides/Guide_30_Using_docker_to_deploy_fastkafka']}, {'Benchmarking': ['guides/Guide_06_Benchmarking_FastKafka']}]},
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

    "LICENSE",
    "CONTRIBUTING",
    "CHANGELOG",
],
};