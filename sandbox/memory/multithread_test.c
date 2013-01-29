#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NUM_THREADS 4
#define ALLOCATED_SIZE (200*1024)

void * worker(void * threadID) {
  int iterations = 300000;
  while(iterations--) {
    void * p = malloc(ALLOCATED_SIZE);
    memset(p, 0, ALLOCATED_SIZE);
    free(p);
  }
  pthread_exit(NULL);
}

int main(int argc, char** argv) {
  pthread_t threads[NUM_THREADS];
  unsigned int t;
  for (t = 0; t < NUM_THREADS; ++t) {
    printf("Creating thread %d\n", t);
    int rc = pthread_create(&threads[t], NULL, worker, NULL);
    if (rc) {
      printf("ERROR: pthread_create returned %d\n", rc);
    }
  }

  pthread_exit(NULL);
}
