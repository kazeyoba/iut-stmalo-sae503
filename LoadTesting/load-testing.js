import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 1000,
  duration: '5m', // Test exécuté pendant 5 minutes
};

export default function () {
  http.get('http://sae503-prod.kaze-cloud.fr/quotes');
  sleep(1);
}
