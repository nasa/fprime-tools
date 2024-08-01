module A {
    constant B = 1
    constant C = 0x44
    constant D = "hello"

    instance E: Component.A base id 0x4444
    instance F: Component.B base id 0x5555 \
        queue size 10

    topology G {
        import I
        
        instance E
        instance F

        connections H {
            E.pout -> F.pin
        }
    }
}