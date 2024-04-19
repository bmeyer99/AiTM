const initialData = {
    tasks: {
        'task-1': { id: 'task-1', content: 'Take out the garbage' },
        'task-2': { id: 'task-2', content: 'Watch my favorite show' },
        'task-3': { id: 'task-3', content: 'Charge my phone' },
        'task-4': { id: 'task-4', content: 'Cook dinner' }
    },
    stages: {
        'stage-1': {
            id: 'stage-1',
            title: 'To do',
            taskIds: ['task-1', 'task-2', 'task-3', 'task-4']
        },
        'stage-2': {
            id: 'stage-2',
            title: 'In progress',
            taskIds: []
        },
    },
    stageOrder: ['stage-1', 'stage-2']
};

export default initialData;