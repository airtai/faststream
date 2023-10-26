# test_01.py
# Had to install pytest-asyncio

import sys
from os.path import dirname, realpath
from faststream import FastStream
from faststream.kafka import TestKafkaBroker, KafkaBroker
import pytest

app_path = dirname(dirname(realpath(__file__)))
sys.path.insert(0, app_path)


broker = KafkaBroker("") # Value here won't matter
app = FastStream(broker)

# This is the payload we expect to consume
valid_payload = {
    "user": "John",
    "age": 29
}

# This is an invalid payload (age is a 'string' and not an integer)
invalid_payload = { 
    "user": "John",
    "age": "29"
}


# Inject our payloads into Kafka so we can test how our consumer handles them
@pytest.mark.asyncio
async def test_correct():
    async with TestKafkaBroker(broker) as br:
        await br.publish(valid_payload, "test-topic") # Publish our valid payload
        with pytest.raises(ValueError): # Tell pytest we expect an error
            await br.publish(invalid_payload, "test-topic") # Publish our invalid payload


# This is the code tha that will parse our incoming message
# and do 'something' with it
@broker.subscriber("test-topic")
async def handle_msg(test_msg):
    test_dict = dict(test_msg)
    user_name = test_dict.get('user')
    user_age = test_dict.get('age')
    assert user_name == "John"
    if isinstance(user_age, int): # Make sure user_age is an integer
        assert user_age == 29
    else: # Raise an exception
        raise ValueError(f"Integer expected for `user_age` but got {type(user_age)}")

    
# To run: Just run pytest as normal
    
