import React from 'react';
import { createRoot } from 'react-dom/client';
import '@atlaskit/css-reset';
import styled from 'styled-components';
import { DragDropContext, Droppable } from 'react-beautiful-dnd';
import initialData from './initial-data';
import Stage from './stage';

const Container = styled.div`
  display: flex;
`;

class InnerList extends React.PureComponent {
  render() {
    const { stage, taskMap, index } = this.props;
    const tasks = stage.taskIds.map(taskId => taskMap[taskId]);
    return <Stage stage={stage} tasks={tasks} index={index} />;
  }
}

class App extends React.Component {
  state = initialData;

  onDragEnd = result => {
    const { destination, source, draggableId, type } = result;

    if (!destination) {
      return;
    }

    if (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    ) {
      return;
    }

    if (type === 'stage') {
      const newStageOrder = Array.from(this.state.stageOrder);
      newStageOrder.splice(source.index, 1);
      newStageOrder.splice(destination.index, 0, draggableId);

      const newState = {
        ...this.state,
        stageOrder: newStageOrder,
      };
      this.setState(newState);
      return;
    }

    const home = this.state.stages[source.droppableId];
    const foreign = this.state.stages[destination.droppableId];

    if (home === foreign) {
      const newTaskIds = Array.from(home.taskIds);
      newTaskIds.splice(source.index, 1);
      newTaskIds.splice(destination.index, 0, draggableId);

      const newHome = {
        ...home,
        taskIds: newTaskIds,
      };

      const newState = {
        ...this.state,
        stages: {
          ...this.state.stages,
          [newHome.id]: newHome,
        },
      };

      this.setState(newState);
      return;
    }

    // moving from one list to another
    const homeTaskIds = Array.from(home.taskIds);
    homeTaskIds.splice(source.index, 1);
    const newHome = {
      ...home,
      taskIds: homeTaskIds,
    };

    const foreignTaskIds = Array.from(foreign.taskIds);
    foreignTaskIds.splice(destination.index, 0, draggableId);
    const newForeign = {
      ...foreign,
      taskIds: foreignTaskIds,
    };

    const newState = {
      ...this.state,
      stages: {
        ...this.state.stages,
        [newHome.id]: newHome,
        [newForeign.id]: newForeign,
      },
    };
    this.setState(newState);
  };

  render() {
    return (
      <DragDropContext onDragEnd={this.onDragEnd}>
        <Droppable
          droppableId="all-stages"
          direction="horizontal"
          type="stage"
        >
          {provided => (
            <Container
              {...provided.droppableProps}
              ref={provided.innerRef}
            >
              {this.state.stageOrder.map((stageId, index) => {
                const stage = this.state.stages[stageId];

                return (
                  <InnerList
                    key={stage.id}
                    stage={stage}
                    index={index}
                    taskMap={this.state.tasks}
                  />
                );
              })}
              {provided.placeholder}
            </Container>
          )}
        </Droppable>
      </DragDropContext>
    );
  }
}


const root = createRoot(document.getElementById('root'));
root.render(<App />);