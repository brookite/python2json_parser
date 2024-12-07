#include <stdio.h>

int func(int x, int y) {
	return x + y;
}

void main() {
	printf("Main function!!!1");
	
	int a;
	a = 10;
	if (a < func(1, 2) + 100) { // if-test1 
		a = 30;
	} else if (a > 5) {
		a = 45;
	} else {
	}
	
	for (int i = 0; i < (10 + 5); i+=func(0) * 2) { //for-test
		printf("1");
		break;
	}

	for (;;a++) {
		while (a - func(2, 3) > 0) { // while-test
			a--;
		}
		
	}
	
	while (a > 0) { // while-test
		a--;
	}
	
	func(1, 2);
	int y = func(1, func(2, 3)) + func(4, func(func(5, 6), 7));
	
	{
		int a = 4;
		a = 5;
	}
}
