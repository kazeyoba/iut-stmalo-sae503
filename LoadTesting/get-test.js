import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  iterations: 10,
};

export default function () {
  
  http.get('https://sae503-prod.kaze-cloud.fr/quotes');

  sleep(1);
}