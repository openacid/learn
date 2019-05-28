# golang convention


## 0. firstly, consult with [golang code review comments](https://github.com/golang/go/wiki/CodeReviewComments)


## 1. it's no need to define variable name for function's return value, define variable type only

In golang, function's return variable name may cause a 'xxx is shadowed during return' error.


There is a bad usage, which get a `err is shadowed during return` error.

**BAD**:
```go
func getPrimeNumberBefore(n int) (rst []int, err error) {
    for i := 2; i < n; i++ {
        // err declared in return value is shadowed.
        found, err := isPrime(i)
        if err != nil {
            return
        }

        if found {
            rst = append(rst, i)
        }
    }

    return
}
```


There are our recommanded usage:

**GOOD**:
```go
func getPrimeNumberBefore(n int) ([]int, error) {

    var rst []int
    var err error
    for i := 2; i < n; i++ {
        found, err := isPrime(i)
        if err != nil {
            return rst, err
        }

        if found {
            rst = append(rst, i)
        }
    }

    return rst, err
}
```
