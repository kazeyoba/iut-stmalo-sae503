import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 10 },   // Charge faible
    { duration: '10s', target: 500 },  // Pic soudain
    { duration: '10s', target: 10 },   // Retour à faible charge
    { duration: '10s', target: 1000 }, // Deuxième pic encore plus intense
    { duration: '30s', target: 10 },    // Retour à zéro
  ],
};

export default function () {
  http.get('http://sae503-prod.kaze-cloud.fr/quotes');
  sleep(1);
}
