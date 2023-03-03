
from pydantic import BaseModel, NonNegativeFloat, Field

class IrisInputData(BaseModel):
    sepal_length: NonNegativeFloat = Field(
        ..., example=0.5, description="Sepal length in cm"
    )
    sepal_width: NonNegativeFloat = Field(
        ..., example=0.5, description="Sepal width in cm"
    )
    petal_length: NonNegativeFloat = Field(
        ..., example=0.5, description="Petal length in cm"
    )
    petal_width: NonNegativeFloat = Field(
        ..., example=0.5, description="Petal width in cm"
    )


class IrisPredictionData(BaseModel):
    species: str = Field(..., example="setosa", description="Predicted species")
    
from fastkafka.application import FastKafka

kafka_app = FastKafka()

iris_species = ["setosa", "versicolor", "virginica"]

@kafka_app.consumes(topic="input_data", auto_offset_reset="latest")
async def on_input_data(msg: IrisInputData):
    global model
    species_class = model.predict([
          [msg.sepal_length, msg.sepal_width, msg.petal_length, msg.petal_width]
        ])[0]

    to_predictions(species_class)


@kafka_app.produces(topic="predictions")
def to_predictions(species_class: int) -> IrisPredictionData:
    prediction = IrisPredictionData(species=iris_species[species_class])
    return prediction
