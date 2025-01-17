import {gql, useMutation} from '@apollo/client';
import {TextArea} from '@blueprintjs/core';
import {
  ButtonLink,
  ButtonWIP,
  ColorsWIP,
  DialogBody,
  DialogFooter,
  DialogWIP,
  Group,
} from '@dagster-io/ui';
import * as React from 'react';

import 'chartjs-adapter-date-fns';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SharedToaster} from '../app/DomUtils';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {SensorSelector} from '../types/globalTypes';

export const EditCursorDialog: React.FC<{
  cursor: string;
  sensorSelector: SensorSelector;
  onClose: () => void;
}> = ({sensorSelector, cursor, onClose}) => {
  const [cursorValue, setCursorValue] = React.useState(cursor);
  const [isSaving, setIsSaving] = React.useState(false);
  const [requestSet] = useMutation(SET_CURSOR_MUTATION);

  const onSave = async () => {
    setIsSaving(true);
    const {data} = await requestSet({
      variables: {sensorSelector, cursor: cursorValue},
    });
    if (data?.setSensorCursor.__typename === 'Sensor') {
      SharedToaster.show({message: 'Cursor value updated', intent: 'success'});
    } else {
      const error = data.setSensorCursor;
      SharedToaster.show({
        intent: 'danger',
        message: (
          <Group direction="row" spacing={8}>
            <div>Could not set cursor value.</div>
            <ButtonLink
              color={ColorsWIP.White}
              underline="always"
              onClick={() => {
                showCustomAlert({
                  title: 'Python Error',
                  body: <PythonErrorInfo error={error} />,
                });
              }}
            >
              View error
            </ButtonLink>
          </Group>
        ),
      });
    }
    onClose();
  };

  return (
    <DialogWIP
      isOpen={true}
      onClose={onClose}
      style={{
        width: '50vw',
      }}
      title={`Edit ${sensorSelector.sensorName} cursor`}
    >
      <DialogBody>
        <TextArea
          value={cursorValue}
          onChange={(e) => setCursorValue(e.target.value)}
          style={{width: '100%'}}
        />
      </DialogBody>
      <DialogFooter>
        <ButtonWIP onClick={onClose}>Cancel</ButtonWIP>
        <ButtonWIP intent="primary" onClick={onSave} disabled={isSaving}>
          Set cursor value
        </ButtonWIP>
      </DialogFooter>
    </DialogWIP>
  );
};

const SET_CURSOR_MUTATION = gql`
  mutation SetSensorCursorMutation($sensorSelector: SensorSelector!, $cursor: String) {
    setSensorCursor(sensorSelector: $sensorSelector, cursor: $cursor) {
      ... on Sensor {
        id
        sensorState {
          id
          status
          typeSpecificData {
            ... on SensorData {
              lastCursor
            }
          }
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
