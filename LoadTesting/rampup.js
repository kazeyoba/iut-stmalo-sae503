import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '5m', target: 100 },
    { duration: '3m', target: 200 },
    { duration: '5m', target: 0 },
  ],
};

export default function () {
  http.get('http://sae503-prod.kaze-cloud.fr/quotes');
  sleep(1);
}
